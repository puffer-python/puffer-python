# coding=utf-8
import logging
import random
import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class AttributeGroupProvider(faker.providers.BaseProvider):
    def attribute_group(self, set_id=None, system_group=None, level=1, code=None, parent_id=0):
        group = m.AttributeGroup()
        group.name = fake.text()
        group.code = code or fake.unique_str()
        group.priority = fake.integer()
        group.attribute_set_id = set_id
        group.parent_id = parent_id
        group.is_flat = random.choice([0, 1])
        group.level = level
        group.path = group.id if level == 1 else f'{parent_id}/{group.id}'
        group.system_group = random.choice((True, False)) \
                             if system_group is None else system_group
        m.db.session.add(group)
        m.db.session.flush()

        return group
