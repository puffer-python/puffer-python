import logging
from sqlalchemy.orm import load_only
from catalog import models as m, constants
from catalog.utils import safe_cast

__author__ = 'Quang.LM'

_logger = logging.getLogger(__name__)


class ProductGroup:
    def __init__(self, session, sellable_product, all_variant_attributes):
        self.session = session
        self.sellable_product = sellable_product
        self.map_variants, self.map_attribute_values = self.__get_variant_attribute_values(all_variant_attributes)
        self.product_skus = self.__get_skus_of_product()

    def __add_map(self, map_data, key, value):
        values = map_data.get(key)
        if not values:
            values = []
        values.append(value)
        map_data[key] = values

    def __get_variant_attribute_values(self, all_variant_attributes):
        variant_attribute_values = {}
        variants = {}
        for va in all_variant_attributes:
            self.__add_map(variants, va.get('variant_id'), va)
            options = (va.get('attribute') or {}).get('options') or []
            for o in options:
                self.__add_map(variant_attribute_values, (va.get('attribute_id'), o.get('id')),
                               ({'id': va.get('id'), 'variant_id': va.get('variant_id')}))
        return variants, variant_attribute_values

    def __get_base_variant_id(self, variant_id):
        variant = self.session.query(m.ProductVariant).filter(m.ProductVariant.id == variant_id).first()
        all_uom_ratios = variant.all_uom_ratios.split(',')
        if len(all_uom_ratios) <= 1:
            return -1
        for uom_ratio in all_uom_ratios:
            if safe_cast(uom_ratio.split(':')[1], float) == 1.0:
                return safe_cast(uom_ratio.split(':')[0], int)

    def __get_attribute_value(self, variant_attribute, uom_option, base_uom_name):
        attribute = variant_attribute.get('attribute')
        if attribute.get('code') == constants.UOM_RATIO_CODE_ATTRIBUTE:
            value = uom_option.get("value")
            attribute_value = variant_attribute.get('value')
            ratio = safe_cast(attribute_value, float)
            if ratio != 1.0:
                i_ratio = safe_cast(attribute_value, int)
                if i_ratio == ratio:
                    ratio = i_ratio
                value = f'{value} {ratio} {base_uom_name}'
        else:
            value = str.join('', map(lambda x: x.get("value"), attribute.get('options')))
        return {
            'id': variant_attribute.get('id'),
            'code': attribute.get('code'),
            'value': value,
            'option_id': variant_attribute.get('id')
        }

    def __has_ratio_exchange(self):
        for sku in self.product_skus:
            if sku.uom_ratio != constants.BASE_UOM_RATIO:
                return True
        return False

    def __get_skus_of_product(self):
        return self.session.query(m.SellableProduct).filter(
            m.SellableProduct.product_id == self.sellable_product.product_id
        ).options(load_only('sku', 'uom_ratio', 'variant_id', 'editing_status_code')).all()

    def __get_one_sku(self, sku, base_uom_name):
        attribute_values = []
        uom_option = None
        variant_attributes = self.map_variants.get(sku.variant_id, [])
        for va in variant_attributes:
            attribute = va.get('attribute')
            if attribute and attribute.get('code') == constants.UOM_CODE_ATTRIBUTE:
                uom_option = attribute.get('options')[0]
                break
        if uom_option:
            for va in variant_attributes:
                attribute_values.append(self.__get_attribute_value(va, uom_option, base_uom_name))
        return {
            'sku': sku.sku,
            'attribute_values': attribute_values
        }

    def __get_base_uom_name(self, base_variant_id):
        if base_variant_id > 0:
            for va in self.map_variants.get(base_variant_id, []):
                attribute = va.get('attribute')
                if attribute and attribute.get('code') == constants.UOM_CODE_ATTRIBUTE:
                    option = attribute.get('options')[0]
                    return option.get('value')
        return ''

    def __get_and_update_base_variant(self, map_base_variant_id, sku):
        base_variant_id = map_base_variant_id.get(sku.variant_id)
        if not base_variant_id:
            base_variant_id = self.__get_base_variant_id(sku.variant_id)
            map_base_variant_id[sku.variant_id] = base_variant_id
        return base_variant_id

    def __get_option_image(self, variant_ids):
        """
        We always select from database because now not many attributes present by image
        """
        image = self.session.query(m.VariantImage).filter(
            m.VariantImage.product_variant_id.in_(variant_ids),
            m.VariantImage.status == 1, m.VariantImage.is_displayed == 1
        ).order_by(m.VariantImage.priority).first()
        if image:
            return {
                'url': image.url,
                'path': image.path,
                'priority': image.priority
            }

    def __get_attribute_group_attributes(self, group_attributes):
        attribute_group_attributes = []
        for g in group_attributes:
            attribute_group_attributes.extend(g.get('attributes'))
        return attribute_group_attributes

    def __get_exclude_attribute_codes(self):
        if self.__has_ratio_exchange():
            return [constants.UOM_RATIO_CODE_ATTRIBUTE]
        return [constants.UOM_CODE_ATTRIBUTE, constants.UOM_RATIO_CODE_ATTRIBUTE]

    def __get_attribute_option_values(self, attribute, attribute_options):
        attribute_id = attribute.get('attribute_id')
        option_values = []
        attribute_options = sorted(attribute_options, key=lambda x: x.get('priority'))

        for o in attribute_options:
            variant_attributes = self.map_attribute_values.get((attribute_id, o.get('id')))
            if variant_attributes:
                option_image = None
                if attribute.get('variation_display_type') == 'image':
                    variant_ids = list(map(lambda x: x.get('variant_id'), variant_attributes))
                    option_image = self.__get_option_image(variant_ids)
                ids = set(map(lambda x: x.get('id'), variant_attributes))
                option_values.append({
                    'option_id': o.get("id"),
                    'value': f'{o.get("value")} {o.get("unit_code")}'.strip(),
                    'thumbnail_url': o.get('thumbnail_url'),
                    'image': option_image
                })
        return option_values

    def get_variants(self):
        if len(self.product_skus) == 1:
            return None
        variants = []
        map_base_variant_id = {}
        active_skus_of_product = list(filter(lambda x: x.editing_status_code == 'active', self.product_skus))
        for sku in active_skus_of_product:
            base_variant_id = self.__get_and_update_base_variant(map_base_variant_id, sku)
            base_uom_name = self.__get_base_uom_name(base_variant_id)
            variants.append(self.__get_one_sku(sku, base_uom_name))
        return variants

    def get_configurations(self, group_attributes):
        attribute_group_attributes = self.__get_attribute_group_attributes(group_attributes)
        exclude_attr_codes = self.__get_exclude_attribute_codes()
        attributes = []
        for aga in attribute_group_attributes:
            if aga.get('code') in exclude_attr_codes:
                continue
            if aga.get('is_variation') == 1:
                attributes.append(aga)

        configurations = []
        for attr in attributes:
            attribute_id = attr.get('attribute_id')
            attribute_options = attr.get('options') or []
            configurations.append({
                'id': attribute_id,
                'code': attr.get('code'),
                'name': attr.get('name'),
                'option_type': attr.get('variation_display_type'),
                'options': self.__get_attribute_option_values(attr, attribute_options)
            })

        return configurations
