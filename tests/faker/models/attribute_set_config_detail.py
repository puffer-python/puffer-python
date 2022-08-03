# coding=utf-8
import logging
import random
import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class AttributeSetConfigDetailProvider(faker.providers.BaseProvider):
    def attribute_set_config_detail(self, **data):
        config = m.AttributeSetConfigDetail()
        config.field_display = data.get('field_display') or fake.text()
        config.attribute_set_config_id = data.get('config_id') or fake.integer()
        config.priority = fake.integer()
        config.text_before = fake.text()
        config.text_after = fake.text()
        config.object_type = data.get('object_type') or \
                             self.attribute_set_config_objective_type()
        config.object_value = data.get('object_value') or fake.text()

        m.db.session.add(config)
        m.db.session.flush()

        return config

    def attribute_set_config_objective_type(self):
        return random.choice([
            'attribute',
            'attribute_set'
        ])

    def attribute_set_config_default(self, attribute_set_id=None):
        config = m.AttributeSetConfig()
        config.attribute_set_id = attribute_set_id or 1
        config.is_default = 1
        m.db.session.add(config)
        m.db.session.flush()

        return config
