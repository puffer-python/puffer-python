# coding=utf-8
import logging
import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class AttributeSetProvider(faker.providers.BaseProvider):
    def attribute_set(self, **kwargs):
        attr_set = m.AttributeSet()
        attr_set.name = kwargs.get('name', fake.text())
        attr_set.code = fake.unique_str()
        m.db.session.add(attr_set)
        m.db.session.flush()

        return attr_set

    def attribute_set_config(
            self,
            set_id=None,
            brand_id=None,
            attribute_1_id=None,
            attribute_1_value=None,
            attribute_2_id=None,
            attribute_2_value=None,
            attribute_3_id=None,
            attribute_3_value=None,
            attribute_4_id=None,
            attribute_4_value=None,
            attribute_5_id=None,
            attribute_5_value=None
    ):
        config = m.AttributeSetConfig()
        config.attribute_set_id = set_id
        config.brand_id = brand_id
        config.attribute_1_id = attribute_1_id or fake.integer()
        config.attribute_1_value = attribute_1_value or fake.integer()
        config.attribute_2_id = attribute_2_id or fake.integer()
        config.attribute_2_value = attribute_2_value or fake.integer()
        config.attribute_3_id = attribute_3_id or fake.integer()
        config.attribute_3_value = attribute_3_value or fake.integer()
        config.attribute_4_id = attribute_4_id or fake.integer()
        config.attribute_4_value = attribute_4_value or fake.integer()
        config.attribute_5_id = attribute_5_id or fake.integer()
        config.attribute_5_value = attribute_5_value or fake.integer()

        m.db.session.add(config)
        m.db.session.flush()

        return config
