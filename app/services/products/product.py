# coding=utf-8
# pylint: disable=E0401,E1133,E1111,E0213
import funcy
from flask_login import current_user
from sqlalchemy import func

import config
from catalog import models as m
from catalog import utils
from catalog.extensions.exceptions import NotFoundException, BadRequestException
from catalog.services import Singleton
from .query import ProductQuery
from .variant import get_attributes_by_variant_id
from catalog.services.attribute_sets.attribute_set import get_variant_attribute_by_attribute_set_id
from catalog.constants import MAX_SUB_SKU, SUB_SKU_POSTFIX
from catalog.extensions import signals


def _update_product_detail_by_product_id(product_id):
    skus = m.SellableProduct.query.filter(
        m.SellableProduct.product_id == product_id
    ).all()
    for sellable_product in skus:
        signals.sellable_common_update_signal.send(sellable_product)
        signals.sellable_update_signal.send(sellable_product)
    return {}


def _not_exist_variant_attribute(from_sku, to_sku):
    attributes = get_variant_attribute_by_attribute_set_id(from_sku.attribute_set_id)
    if not attributes:
        return True
    variant_attributes = get_attributes_by_variant_id(from_sku.variant_id, attributes)
    array_attributes = [{'attribute_id': variant_attribute.id, 'value': variant_attribute.value} for variant_attribute
                        in variant_attributes]
    to_variants = m.ProductVariant.query.filter(m.ProductVariant.product_id == to_sku.product_id).all()
    for to_variant in to_variants:
        to_variant_attributes = get_attributes_by_variant_id(to_variant.variant_id, attributes)
        to_array_attributes = [{'attribute_id': to_variant_attribute.id, 'value': to_variant_attribute.value} for
                               to_variant_attribute in to_variant_attributes]
        if array_attributes == to_array_attributes:
            raise BadRequestException(
                'Thuộc tính biến thể của sản phẩm đã tồn tại'
            )
    return True


def _validate_same_product(from_sku, to_sku):
    if from_sku.attribute_set_id != to_sku.attribute_set_id:
        raise BadRequestException(
            'Chỉ có gom nhóm những sản phầm cùng Bộ thuộc tính'
        )

    if from_sku.model != to_sku.model:
        raise BadRequestException(
            'Chỉ có gom nhóm những sản phầm cùng Model'
        )

    if from_sku.brand_id != to_sku.brand_id:
        raise BadRequestException(
            'Chỉ có gom nhóm những sản phầm cùng Thương hiệu'
        )
    return True


class ProductService(Singleton):
    def get_product_list(self, filters, sort_field, sort_order, page, page_size, **kwargs):
        """get_product_list

        :param filters:
        :param sort_field:
        :param sort_order:
        :param page:
        :param page_size:
        """
        query = ProductQuery()
        if 'email' in kwargs:
            query.restrict_by_user(kwargs['email'])
        query.apply_filters(filters)
        total_records = len(query)
        query.sort(sort_field, sort_order)
        query.pagination(page, page_size)
        return query.all(), total_records

    def get_product(self, product_id):
        """get_product

        :param product_id:
        """
        query = ProductQuery()
        query.apply_filters({'id': product_id})
        return query.first()

    def get_draft_product(self):
        return m.Product.query.join(
            m.Category,
            m.Product.category_id == m.Category.id
        ).filter(
            m.Product.editing_status_code == 'draft',
            m.Product.created_by == current_user.email,
            m.Category.seller_id == current_user.seller_id,
        ).first()

    def delete_draft_product(self, email):
        query = ProductQuery()
        product = query.restrict_by_user(email).apply_filters({
            'editing_status_code': 'draft'
        }).first()
        if not product:
            return
        for variant in product.variants:
            for attr in variant.variant_attributes:
                m.db.session.delete(attr)
            for image in variant.images:
                m.db.session.delete(image)
            m.db.session.delete(variant)
        m.db.session.delete(product)
        m.db.session.commit()
        return product

    def __upsert_product_category(self, product_id, category_id, create_by, is_update=True):
        if not category_id:
            return
        category = m.Category.query.filter(m.Category.id == category_id).first()
        product_category = None
        if is_update:
            alias_categories = m.db.aliased(m.Category)
            product_category = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id,
                                                              alias_categories.query.filter(
                                                                  alias_categories.id == m.ProductCategory.category_id,
                                                                  alias_categories.seller_id == category.seller_id
                                                              ).exists()).first()
        if product_category:
            product_category.category_id = category_id
            product_category.created_by = create_by
        else:
            product_category = m.ProductCategory()
            product_category.product_id = product_id
            product_category.category_id = category_id
            product_category.created_by = create_by
            m.db.session.add(product_category)

    def __upsert_product_categories(self, product_id, category_ids, create_by, is_update=True):
        if not category_ids:
            return
        categories = m.Category.query.filter(m.Category.id.in_(category_ids)).all()
        product_categories = None
        old_categories = None
        if is_update:
            product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id).all()
            product_category_ids = list(map(lambda x: x.category_id, product_categories))
            old_categories = m.Category.query.filter(m.Category.id.in_(product_category_ids)).all()
        for category in categories:
            product_category = None
            if is_update:
                old_category_on_seller = next(filter(lambda x: x.seller_id == category.seller_id, old_categories), None)
                if old_category_on_seller:
                    product_category = next(
                        filter(lambda x: x.category_id == old_category_on_seller.id, product_categories), None)
            if product_category:
                product_category.category_id = category.id
                product_category.created_by = create_by
            else:
                product_category = m.ProductCategory()
                product_category.product_id = product_id
                product_category.category_id = category.id
                product_category.created_by = create_by
                m.db.session.add(product_category)

    def create_product(self, data, email):
        """create_product

        :param data:
        """
        data['unit_po_id'] = data.get('unit_id')
        data['spu'] = 'SPU{}'.format(utils.random_string(10))

        # Allow either code or id.
        unit_code = data.pop('unit_code', '')
        if not data.get('unit_id') and unit_code:
            unit = m.Unit.query.filter(m.Unit.code == unit_code).first()
            data['unit_id'] = unit.id
            data['unit_po_id'] = unit.id

        # Allow either code or id.
        category_ids = None
        if data.get('category_ids'):
            category_ids = data.pop('category_ids')
            data['category_id'] = category_ids[0]
        else:
            category_code = data.pop('category_code', '')
            if not data['category_id']:
                category = m.Category.query.filter(m.Category.code == category_code).first()
                data['category_id'] = category.id if category else None

        # Get attribute_set_id from default platform category
        if data.get('category_id') and not data.get('attribute_set_id'):
            category = m.Category.query.get(data['category_id'])
            data['attribute_set_id'] = category.default_attribute_set.id if category.default_attribute_set else None

        # Allow either code or id.
        brand_code = data.pop('brand_code', '')
        if not data['brand_id']:
            brand = m.Brand.query.filter(m.Brand.code == brand_code).first()
            data['brand_id'] = brand.id

        product = m.Product(**data)
        product.url_key = utils.convert(utils.slugify(data['name']))
        product.created_by = email
        m.db.session.add(product)
        m.db.session.flush()
        if category_ids:
            self.__upsert_product_categories(product.id, category_ids, email, is_update=False)
        elif data.get('category_id'):
            self.__upsert_product_category(product.id, data.get('category_id'), email, is_update=False)

        m.db.session.commit()
        return product

    def _update_name_of_product_variants(self, new_name, product_id):
        product_name = m.Product.query.get(product_id).name

        product_variants = m.ProductVariant.query.filter_by(
            product_id=product_id
        ).all()

        for variant in product_variants:
            variant.name = str(variant.name).replace(product_name, new_name)

    def update_product(self, data, product_id):
        if data.get('name'):
            self._update_name_of_product_variants(data.get('name'), product_id)

        category_ids = None
        if data.get('category_ids'):
            category_ids = data.pop('category_ids')
            data['category_id'] = category_ids[0]

        m.Product.query.filter(
            m.Product.id == product_id
        ).update(data, synchronize_session=False)

        if category_ids:
            self.__upsert_product_categories(product_id, category_ids, data.get('created_by'))
        elif data.get('category_id'):
            self.__upsert_product_category(product_id, data['category_id'], data.get('created_by'))

        m.db.session.commit()

        product = m.Product.query.filter(
            m.Product.id == product_id
        ).first()

        return product

    def get_product_history(self, sellable_id=None, sku=None):
        if sellable_id:
            sellable_product = m.SellableProduct.query.filter(
                m.SellableProduct.id == sellable_id,
                m.SellableProduct.seller_id == current_user.seller_id
            ).first()
        else:
            sellable_product = m.SellableProduct.query.filter(
                m.SellableProduct.sku == sku,
                m.SellableProduct.seller_id == current_user.seller_id
            ).first()

        if not sellable_product:
            raise NotFoundException("Không tìm thấy sản phẩm, hoặc sản phẩm không nằm trong seller của bạn")

        histories = m.ProductLog.query.filter(
            m.ProductLog.sku == sellable_product.sku
        ).order_by(m.ProductLog.id.desc()).all()
        return {
            "histories": histories
        }

    def move_group(selft, from_sku, to_sku):
        """
        Move a sku from a to b
        """

        from_sellable_product = m.SellableProduct.query.filter(
            m.SellableProduct.sku == from_sku
        ).first()
        to_sellable_product = m.SellableProduct.query.filter(
            m.SellableProduct.sku == to_sku
        ).first()
        if from_sellable_product and to_sellable_product and _validate_same_product(
                from_sellable_product,
                to_sellable_product
        ) and _not_exist_variant_attribute(from_sellable_product, to_sellable_product):
            old_product_id = from_sellable_product.product_id
            product_id = to_sellable_product.product_id
            from_sellable_product.product_id = product_id
            from_sellable_product.product_variant.product_id = product_id
            m.db.session.commit()
            _update_product_detail_by_product_id(old_product_id)
            _update_product_detail_by_product_id(product_id)
            return {}

        raise BadRequestException(
            'Không tìm thấy sản phẩm hoặc thông tin không chính xác'
        )

    @staticmethod
    def _gen_sub_sku(sku):
        total_query = m.db.session.query(func.count(m.SellableProductSubSku.id)).filter(
            m.SellableProductSubSku.sellable_product_id == sku.id
        )
        total = m.db.session.execute(total_query).scalar()
        if total >= MAX_SUB_SKU:
            raise BadRequestException('Sản phẩm đã có {} sản phẩm con'.format(MAX_SUB_SKU))
        return '{}{}{}'.format(sku.sku, SUB_SKU_POSTFIX, total + 1)

    def create_sub_sku(self, sku, created_by=''):
        sellable_product = m.SellableProduct.query.filter(
            m.SellableProduct.sku == sku,
        ).first()
        if sellable_product:
            sub_sku_code = self._gen_sub_sku(sellable_product)
            sub_sku = m.SellableProductSubSku(
                sellable_product_id=sellable_product.id,
                sub_sku=sub_sku_code,
                created_by=created_by
            )
            m.db.session.add(sub_sku)
            sellable_product.updated_by = created_by
            m.db.session.flush()
            signals.sub_sku_created_signal.send(sub_sku, updated_by=created_by)
            m.db.session.commit()
            return {
                'sku': sub_sku_code
            }
        raise NotFoundException("Không tìm thấy sản phẩm, hoặc sản phẩm không nằm trong seller của bạn")


def delete_product(p_id, delete_all_sku=False):
    product = m.Product.query.get(p_id)
    if not product:
        return
    m.ProductVariant.query.filter(
        m.ProductVariant.product_id == p_id
    ).delete(synchronize_session='fetch')

    m.ProductCategory.query.filter(
        m.ProductCategory.product_id == p_id
    ).delete(synchronize_session='fetch')

    if delete_all_sku:
        m.SellableProduct.query.filter(
            m.SellableProduct.product_id == p_id
        ).delete(synchronize_session='fetch')

    m.db.session.delete(product)
    m.db.session.commit()
    return product


def get_psd_product():
    attr_code = m.Attribute.query.filter(
        m.Attribute.code == 'phanmem_model'
    ).first()
    if attr_code:
        import requests as rq
        psd_code = rq.get(config.MAGENTO_HOST + '/api-v2/product/psd').json()
        products = m.SellableProduct.query.join(
            m.VariantAttribute,
            m.VariantAttribute.variant_id == m.SellableProduct.variant_id
            and m.VariantAttribute.attribute_id == attr_code.id
        ).filter(m.VariantAttribute.value.in_(psd_code))
        return funcy.lpluck_attr('sku', products)
    return []
