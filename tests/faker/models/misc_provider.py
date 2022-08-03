# coding=utf-8
import logging
import random

import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class MiscProvider(faker.providers.BaseProvider):
    """

    """
    def data_type(self):
        return random.choice([
            'objective',
            'selling_status',
            'editing_status'
        ])

    def misc(self, data_type=None, code=None, config=None, name=None):
        """
        Create misc record of specific type
        :param data_type:
        :param config:
        :return:
        """
        misc = m.Misc()
        misc.type = data_type or fake.data_type()
        misc.name = name or fake.text()
        misc.code = code or fake.unique_str()
        misc.config = config

        m.db.session.add(misc)
        m.db.session.flush()

        return misc
