import logging
from catalog import models as m
from catalog.extensions.ram_queue_consumer.functions.utils import get_variant_attribute_value, get_default

__author__ = 'Quang.LM'

_logger = logging.getLogger(__name__)

_NUMBER_SET_CONFIG_ATTRIBUTES = 5


class SeoConfig:
    def __init__(self, session, sellable_product):
        self.session = session
        self.sellable_product = sellable_product
        self.match_config = None

    def __order_attribute_set_configs(self, query):
        return query.order_by(m.AttributeSetConfig.attribute_5_id.desc(), m.AttributeSetConfig.attribute_4_id.desc(),
                              m.AttributeSetConfig.attribute_3_id.desc(), m.AttributeSetConfig.attribute_2_id.desc(),
                              m.AttributeSetConfig.attribute_1_id.desc(), m.AttributeSetConfig.brand_id.desc())

    def __get_default_seo_config(self):
        query = self.__order_attribute_set_configs(self.session.query(m.AttributeSetConfig).filter(
            m.AttributeSetConfig.attribute_set_id == self.sellable_product.attribute_set_id,
            m.AttributeSetConfig.is_default == 1))
        return query.first()

    def __get_compare_variant_attributes(self, variant_attributes, attribute_id, value):
        if not attribute_id and not value:
            return 0
        for va in variant_attributes:
            if va.get('attribute_id') == attribute_id and va.get('value') == value:
                return 0
        return 1

    def __get_seo_config(self, variant_attributes):
        if self.match_config:
            return self.match_config
        query = self.__order_attribute_set_configs(self.session.query(m.AttributeSetConfig).filter(
            m.AttributeSetConfig.attribute_set_id == self.sellable_product.attribute_set_id,
            m.AttributeSetConfig.is_deleted == 0))
        set_configs = query.all()
        for config in set_configs:
            if config.brand_id and config.brand_id != self.sellable_product.brand_id:
                continue
            for i in range(_NUMBER_SET_CONFIG_ATTRIBUTES):
                attribute_id = getattr(config, f'attribute_{i + 1}_id')
                value = getattr(config, f'attribute_{i + 1}_value')
                compare_value = self.__get_compare_variant_attributes(variant_attributes, attribute_id, value)
                if compare_value == 0:
                    self.match_config = config
                    return config

    def __get_seo_by_attribute(self, map_variant_attributes, object_value):
        variant_value = map_variant_attributes.get(object_value)
        if variant_value:
            return get_variant_attribute_value(variant_value)

    def __get_seo_by_type(self, object_type, object_value):
        sellable_product = self.sellable_product
        if object_type == 'product_name':
            return sellable_product.name
        if object_type == 'attribute_set':
            attr_set = self.session.query(m.AttributeSet).filter(
                m.AttributeSet.id == sellable_product.attribute_set_id).first()
            if attr_set:
                return attr_set.name
        if object_type == 'brand':
            brand = self.session.query(m.Brand).filter(m.Brand.id == sellable_product.brand_id).first()
            if brand:
                return brand.name
        if object_type == 'sku':
            return sellable_product.sku
        if object_type == 'warranty' and sellable_product.warranty_months:
            return f'{sellable_product.warranty_months} tháng'
        if object_type == 'model':
            return sellable_product.model
        if object_type == 'part_number':
            return sellable_product.part_number
        if object_type == 'text':
            return object_value

    def __get_seo(self, attribute_set_config_id, variant_attributes):
        def _get_map_variant_attributes():
            __map_variant_attributes = {}
            for va in variant_attributes:
                __map_variant_attributes[str(va.get('attribute_id'))] = va
            return __map_variant_attributes

        config_details = self.session.query(m.AttributeSetConfigDetail).filter(
            m.AttributeSetConfigDetail.attribute_set_config_id == attribute_set_config_id) \
            .order_by(m.AttributeSetConfigDetail.priority).all()
        map_seo = {}
        map_variant_attributes = _get_map_variant_attributes()
        for config in config_details:
            values = map_seo.get(config.field_display) or []
            if config.object_type == 'attribute':
                value = self.__get_seo_by_attribute(map_variant_attributes, config.object_value)
            else:
                value = self.__get_seo_by_type(config.object_type, config.object_value)
            if value is not None:
                values.append(f'{get_default(config.text_before)}{value}{get_default(config.text_after)}')
                map_seo[config.field_display] = values

        response = {}
        for k, v in map_seo.items():
            response[k] = str.join('', v)

        return response

    def __compare(self, v1, v2):
        if not v1 and not v2:
            return False
        if not v1:
            return False
        if not v2:
            return True
        return v1 > v2

    def __get_seo_default(self, default_config, match_config):
        if not match_config:
            return default_config
        if not default_config:
            return match_config
        for i in range(_NUMBER_SET_CONFIG_ATTRIBUTES):
            default_attribute_id = getattr(default_config, f'attribute_{_NUMBER_SET_CONFIG_ATTRIBUTES - i}_id')
            match_attribute_id = getattr(match_config, f'attribute_{_NUMBER_SET_CONFIG_ATTRIBUTES - i}_id')
            if match_attribute_id and self.__compare(match_attribute_id, default_attribute_id):
                return match_config
        return default_config

    def get_seo_default(self, variant_attributes):
        default_config = self.__get_default_seo_config()
        match_config = self.__get_seo_config(variant_attributes)
        attribute_set_config = self.__get_seo_default(default_config, match_config)
        if attribute_set_config:
            return self.__get_seo(attribute_set_config.id, variant_attributes)
        return {}

    def get_seo_by_config(self, variant_attributes):
        attribute_set_config = self.__get_seo_config(variant_attributes)
        if attribute_set_config:
            return self.__get_seo(attribute_set_config.id, variant_attributes)
        return {}
