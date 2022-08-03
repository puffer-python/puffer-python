# coding=utf-8
from typing import List
import uuid
import funcy
from flask_login import current_user
from sqlalchemy import func
from sqlalchemy.orm import (
    joinedload, load_only
)

from catalog import (
    models,
    utils,
)
from catalog.constants import BASE_UOM_RATIO
from catalog.services import Singleton
from catalog.extensions import signals
from catalog.services.products import VariantQuery
from catalog.utils import decapitalize, safe_cast
from catalog import constants


def get_attributes_by_variant_id(variant_id, attributes):
    models.VariantAttribute.query.filter(
        models.VariantAttribute.variant_id == variant_id,
        models.VariantAttribute.attribute_id.in_(
            funcy.lpluck_attr('id', attributes)
        )
    ).order_by(models.Attribute.id.asc()).all()


def load_all_variant_attributes(product_id):
    """Tải thông tin cần thiết của toàn bộ variant
    Cấu trúc dữ liệu trả về
    {
        "<variant_id>": {
            "<attribute_id>": <value>
        }
    }

    :param product_id:
    """
    from itertools import groupby
    from operator import itemgetter

    product = models.Product.query.get(product_id)
    attributes = models.Attribute.query.join(
        models.AttributeGroupAttribute,
        models.AttributeGroupAttribute.attribute_id == models.Attribute.id
    ).join(
        models.AttributeGroup,
        models.AttributeGroup.id == models.AttributeGroupAttribute.attribute_group_id
    ).filter(
        models.AttributeGroup.attribute_set_id == product.attribute_set_id,
        models.AttributeGroupAttribute.is_variation == 1
    ).all()
    variant_attr_ids = list(map(lambda x: x.id, attributes))

    variants = models.db.session.query(
        models.ProductVariant.id,
        models.VariantAttribute.attribute_id,
        models.VariantAttribute.value
    ).join(
        models.VariantAttribute
    ).filter(
        models.ProductVariant.product_id == product_id,
        models.VariantAttribute.attribute_id.in_(variant_attr_ids),
    ).all()
    data = {variant_id: {attr_id: value for _, attr_id, value in group}
            for variant_id, group in groupby(variants, key=itemgetter(0))}
    return data


def delete_images(data, auto_commit=True):
    list_ids = [item.get('id') for item in data.get('variants')]

    models.VariantImage.query.filter(
        models.VariantImage.product_variant_id.in_(list_ids)
    ).delete(synchronize_session=False)

    if auto_commit:
        models.db.session.commit()


def update_image(variant_id, image_data, created_by=None, auto_commit=True):
    priority = 0
    for image in image_data:
        priority += 1
        variant_image = models.VariantImage()
        variant_image.product_variant_id = variant_id
        variant_image.url = image.get('url')
        variant_image.label = image.get('alt_text')
        variant_image.is_displayed = image.get('allow_display', True)
        variant_image.priority = priority
        variant_image.created_by = created_by or current_user.email
        variant_image.updated_by = created_by or current_user.email

        models.db.session.add(variant_image)

    if auto_commit:
        models.db.session.commit()

    for sku in models.SellableProduct.query.filter(
            models.SellableProduct.variant_id == variant_id
    ).all():
        signals.sellable_update_signal.send(sku)


def _update_uom(variant, uom_data):
    """
    Create new variant attributes from uom attribute and uom_ratio attribute.
    :param variant:
    :param uom_data:
    :return:
    """
    uom_attr = models.Attribute.query.filter(
        models.Attribute.code == 'uom'
    ).first()
    ratio_attr = models.Attribute.query.filter(
        models.Attribute.code == 'uom_ratio'
    ).first()
    uom_variant_attr = models.VariantAttribute.query \
        .filter(
        models.VariantAttribute.variant_id == variant.id,
        models.VariantAttribute.attribute_id == uom_attr.id
    ).first()

    # Create uom_ratio attribute
    uom_ratio_attr = models.VariantAttribute()
    uom_ratio_attr.variant_id = variant.id
    uom_ratio_attr.attribute_id = ratio_attr.id
    uom_ratio_attr.value = uom_data['ratio']
    models.db.session.add(uom_ratio_attr)
    models.db.session.commit()

    # Update all_uom_ratios
    base_uom = models.ProductVariant.query.filter(
        models.ProductVariant.id == uom_data['base']
    ).first()
    if f'{variant.id}:{float(uom_data["ratio"])}' not in base_uom.all_uom_ratios:
        base_uom.all_uom_ratios += f'{variant.id}:{float(uom_data["ratio"])},'
    uom_variants = models.ProductVariant.query.filter(
        models.ProductVariant.id.in_(base_uom.extract_uom_ids())
    ).all()
    for uom_variant in uom_variants:
        uom_variant.all_uom_ratios = base_uom.all_uom_ratios

    # Regenerate variant name
    if float(uom_ratio_attr.value) != BASE_UOM_RATIO:
        base_uom_variant_attr = models.VariantAttribute.query.filter(
            models.VariantAttribute.variant_id == uom_data['base'],
            models.VariantAttribute.attribute_id == uom_attr.id
        ).first()
        variant.name = '{} {} {} {}'.format(
            uom_variant_attr.get_value().value.capitalize(),
            uom_ratio_attr.value,
            base_uom_variant_attr.get_value().value,
            decapitalize(variant.name)
        )

    models.db.session.commit()
    variant.uom = {
        'base': variant.base_uom_id,
        'ratio': uom_ratio_attr.value
    }


class ProductVariantService(Singleton):
    def create_variant(self, product_id, email, attributes_data=None, name=None, auto_commit=False):
        """create_variant

        :param product_id:
        :param attributes:
        """

        def _is_not_uom_and_ratio_attr(variant_attr):
            return variant_attr.attribute.code not in (constants.UOM_CODE_ATTRIBUTE,
                                                       constants.UOM_RATIO_CODE_ATTRIBUTE)

        variant = models.ProductVariant(product_id=product_id)
        models.db.session.add(variant)
        models.db.session.flush()
        if auto_commit:
            models.db.session.commit()

        variant_attributes = list()
        if attributes_data:
            for attribute_data in attributes_data:
                variant_attribute = models.VariantAttribute(
                    variant_id=variant.id,
                    attribute_id=attribute_data['id'],
                    value=str(attribute_data['value']),
                )
                models.db.session.add(variant_attribute)
                models.db.session.flush()
                if auto_commit:
                    models.db.session.commit()
                variant_attributes.append(variant_attribute)

            if not name:
                suffix_var_name = ', '.join(
                    [str(attr.get_value()) if attr.attribute.code == constants.UOM_RATIO_CODE_ATTRIBUTE
                    else attr.get_value().value
                    for attr in variant_attributes if _is_not_uom_and_ratio_attr(attr)])
                name = f'{variant.product.name} ({suffix_var_name})' if suffix_var_name else variant.product.name

        variant.name = name or variant.product.name
        variant.url_key = utils.generate_url_key(variant.name)
        variant.code = utils.random_string(9)
        variant.created_by = email
        models.db.session.flush()

        if auto_commit:
            models.db.session.commit()

        return variant, variant_attributes

    def __get_attribute_ratio_of_variant(self, map_attributes, uom_attr, ratio_attr):
        exclude_attribute_ids = (uom_attr.id, ratio_attr.id)
        attributes = []
        ratio = None
        for attribute_id, value in map_attributes.items():
            if attribute_id not in exclude_attribute_ids:
                item = {
                    'id': attribute_id,
                    'value': value
                }
                attributes.append(item)
            if attribute_id == ratio_attr.id:
                ratio = safe_cast(value, float)
        attributes.sort(key=lambda x: x['id'])
        return attributes, ratio

    def __get_map_variants(self, all_variants, uom_attr, ratio_attr):
        response = {}
        for variant_id, map_attributes in all_variants.items():
            attributes, ratio = self.__get_attribute_ratio_of_variant(map_attributes, uom_attr, ratio_attr)
            key = str(attributes)
            variants = response.get(key, [])
            variants.append({
                'variant_id': variant_id,
                'ratio': ratio
            })
            response[key] = variants
        return response

    def __get_attribute_of_variant(self, variant_id, all_variants, uom_attr, ratio_attr):
        map_attributes = all_variants.get(variant_id) or {}
        attributes, _ = self.__get_attribute_ratio_of_variant(map_attributes, uom_attr, ratio_attr)
        return str(attributes)

    def __update_all_uom_ratios(self, base_variant_id, group_variants):
        base_variant = models.ProductVariant.query.filter(
            models.ProductVariant.id == base_variant_id).first()
        if not base_variant:
            return
        base_variant.all_uom_ratios = ''
        for gr_variant in group_variants:
            uom_ratios = f'{gr_variant["variant_id"]}:{gr_variant["ratio"]}'
            base_variant.all_uom_ratios += f'{uom_ratios},'

            uom_variants = models.ProductVariant.query.filter(
                models.ProductVariant.id.in_(base_variant.extract_uom_ids())
            ).all()

            for uom_variant in uom_variants:
                uom_variant.all_uom_ratios = base_variant.all_uom_ratios

    def __update_variant_name(self, base_variant_id, variant, uom_attr, ratio_attr):
        variant_id = variant.id
        base_uom_variant = models.VariantAttribute.query \
            .filter(
            models.VariantAttribute.variant_id == base_variant_id,
            models.VariantAttribute.attribute_id == uom_attr.id
        ).first()

        uom_variant_attr = models.VariantAttribute.query \
            .filter(
            models.VariantAttribute.variant_id == variant_id,
            models.VariantAttribute.attribute_id == uom_attr.id
        ).first()

        uom_ratio_attr = models.VariantAttribute.query \
            .filter(
            models.VariantAttribute.variant_id == variant_id,
            models.VariantAttribute.attribute_id == ratio_attr.id
        ).first()
        if not uom_variant_attr or not uom_ratio_attr:
            return

        if variant_id != base_variant_id:
            variant_name = '{} {} {}'.format(
                uom_ratio_attr.value,
                base_uom_variant.get_option_value(),
                decapitalize(variant.name)
            )
            if safe_cast(uom_variant_attr.value, int) != safe_cast(base_uom_variant.value, int):
                variant_name = f'{uom_variant_attr.get_option_value().capitalize()} {variant_name}'
            variant.name = variant_name
            variant.url_key = utils.generate_url_key(variant.name)

    def __update_uoms(self, product_id, variants):
        uom_attr = models.Attribute.query.filter(
            models.Attribute.code == constants.UOM_CODE_ATTRIBUTE
        ).first()
        ratio_attr = models.Attribute.query.filter(
            models.Attribute.code == constants.UOM_RATIO_CODE_ATTRIBUTE
        ).first()
        if not uom_attr or not ratio_attr:
            return
        all_variants = load_all_variant_attributes(product_id)
        map_variants = self.__get_map_variants(all_variants, uom_attr, ratio_attr)
        for variant_id, data in variants.items():
            variant_key = self.__get_attribute_of_variant(variant_id, all_variants, uom_attr, ratio_attr)
            group_variants = map_variants.get(variant_key) or []
            base_variant_attribute = next(filter(lambda x: safe_cast(x['ratio'], float)
                                                           == 1.0, group_variants), None)
            if not base_variant_attribute:
                continue

            base_variant_id = base_variant_attribute['variant_id']

            self.__update_all_uom_ratios(base_variant_id, group_variants)
            if not data.get('is_given_name'):
                self.__update_variant_name(base_variant_id, data['variant'], uom_attr, ratio_attr)

    def create_variants(self, product_id, variants_data: List[dict], email, **kwargs):
        """create_variants

        :param product_id:
        :param variants_data:
        :param email:
        """
        ratio_attr = models.Attribute.query.filter(
            models.Attribute.code == constants.UOM_RATIO_CODE_ATTRIBUTE
        ).first()
        variants = list()
        map_variants = {}
        if variants_data:
            for variant_data in variants_data:
                ratio = 0
                attributes_data = variant_data['attributes']
                given_name = variant_data.get('name')
                for attr in attributes_data:
                    if attr['id'] == ratio_attr.id:
                        ratio = attr['value']
                        break
                variant, _ = self.create_variant(
                    product_id=product_id,
                    attributes_data=attributes_data,
                    email=email,
                    name=given_name,
                    auto_commit=kwargs.get('auto_commit'),
                )
                variants.append({
                    'id': variant.id,
                    'name': variant.name,
                    'code': variant.code,
                    'url_key': variant.url_key,
                    'editing_status_code': variant.editing_status_code,
                    'attributes': variant_data['attributes']
                })
                map_variants[variant.id] = {
                    'ratio': ratio,
                    'variant': variant,
                    'is_given_name': bool(given_name),
                }
        else:
            # create default variant for product dont has variation attributes
            variant, _ = self.create_variant(product_id, email)
            variants.append({
                'id': variant.id,
                'name': variant.name,
                'code': variant.code,
                'url_key': variant.url_key,
                'editing_status_code': variant.editing_status_code,
            })
            map_variants[variant.id] = {
                'ratio': 0,
                'variant': variant
            }
        self.__update_uoms(product_id, map_variants)
        product = models.Product.query.get(product_id)
        product.default_variant_id = variants[0]['id']
        if not kwargs.get('__not_bulk_commit'):
            models.db.session.commit()
        else:
            models.db.session.flush()
        return variants

    def update_variant(self, data, created_by=None):
        """
         Perform update on the variants:
             - Deletes old data from db and insert the new ones.
             - If uom data is presented, updates uom attribute and stores uom combination
             in all_uom_ratios.
         :param data:
         :return: list[models.ProductVariants]
         """
        if data.get('variants'):
            delete_images(data)
            variants = models.ProductVariant.query.filter(
                models.ProductVariant.id.in_(item['id'] for item in data['variants'])
            ).all()
            for variant, variant_data in zip(
                    sorted(variants, key=lambda x: x.id),
                    sorted(data['variants'], key=lambda x: x['id'])
            ):
                update_image(variant.id, variant_data.get('images') or [], created_by=created_by)
            return variants

    def create_variant_images_from_external_url(self, data):
        request_id = uuid.uuid4()

        signals.create_variant_images_signal.send({
            'request_id': request_id,
            'variant': data,
            'email': current_user.email
        })

        return request_id

    def upsert_variant_attributes(self, variant_id, attributes_data, upserted_by: str = None):
        variant_attributes = list()
        for data in attributes_data:
            variant_attribute = models.VariantAttribute.query.filter(
                models.VariantAttribute.variant_id == variant_id,
                models.VariantAttribute.attribute_id == data['id']
            )
            if data['value'] in ([], None):
                variant_attribute.delete()
            else:
                variant_attribute = variant_attribute.first()
                if not variant_attribute:
                    variant_attribute = models.VariantAttribute(
                        variant_id=variant_id,
                        attribute_id=data['id'],
                    )
                variant_attribute.set_value(data['value'])

                models.db.session.add(variant_attribute)
                variant_attributes.append(variant_attribute)
        models.db.session.flush()

        sellables = models.SellableProduct.query.filter(
            models.SellableProduct.variant_id == variant_id
        ).all()
        for sellable in sellables:
            signals.sellable_update_signal.send(sellable, created_by=upserted_by)

        return {
            'id': variant_id,
            'attributes': variant_attributes
        }

    def create_bulk_variant_attributes(self, data, created_by: str = None, auto_commit=True):
        variants_data = data['variants']
        variant_values = [self.upsert_variant_attributes(variant_data['id'],
                                                         variant_data['attributes'],
                                                         upserted_by=created_by)
                          for variant_data in variants_data]
        if auto_commit:
            models.db.session.commit()
        return variant_values

    def get_variants(self, filters, page, page_size, sort_field, sort_order):
        base_query = models.db.session.query(models.ProductVariant).join(
            models.SellableProduct,
            models.SellableProduct.variant_id == models.ProductVariant.id
        ).options(load_only(
            'product_id',
            'name',
            'code',
            'url_key',
            'created_by',
            'updated_by',
            'editing_status_code',
            'all_uom_ratios',
            'id',
            'created_at',
            'updated_at'
        ))
        query = VariantQuery(base_query)
        query.apply_filters(filters)
        if sort_field:
            query.sort(sort_field, sort_order)
        total_records = len(query)
        variants = query.pagination(page, page_size).all()

        def _add_number_of_sku(item):
            setattr(item, 'number_of_sku', 1)
            return item

        variants = list(map(_add_number_of_sku, variants))
        return variants, total_records

    def get_variant_attribute_list(self, variant_ids):
        ret = []
        for v_id in variant_ids:
            variant = models.ProductVariant.query.options(
                joinedload('product').load_only('attribute_set_id')
            ).get(v_id)
            attributes = models.VariantAttribute.query.filter(
                models.VariantAttribute.variant_id == variant.id,
            ).options(
                joinedload('attribute')
            ).all()
            ret.append({
                'id': variant.id,
                'attributes': attributes or []
            })
        return ret

    def get_variant(self, v_id):
        return models.ProductVariant.query.filter(models.ProductVariant.id == v_id).first()


variant_svc: ProductVariantService = ProductVariantService.get_instance()


def get_max_priority(p_id):
    max_sku = models.db.session.query(func.max(models.VariantImage.priority)) \
        .filter(models.VariantImage.product_variant_id == p_id) \
        .first()
    return max_sku[0] or 0


def delete_variant(v_id):
    variant = models.ProductVariant.query.filter(
        models.ProductVariant.id == v_id
    ).delete(synchronize_session='fetch')

    models.VariantAttribute.query.filter(
        models.VariantAttribute.variant_id == v_id
    ).delete(synchronize_session='fetch')

    models.SellableProduct.query.filter(
        models.SellableProduct.variant_id == v_id
    ).delete(synchronize_session='fetch')

    models.db.session.commit()
    return variant
