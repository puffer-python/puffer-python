# coding=utf-8
import logging

import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class UnitProvider(faker.providers.BaseProvider):
    """

    """
    def unit(self, name=None, code=None, display_name=None, seller_id=None):
        unit = m.Unit()
        unit.code = code or fake.unique_str()
        unit.name = name or fake.text()
        unit.display_name = display_name or fake.text()
        unit.seller_id = seller_id or 0
        m.db.session.add(unit)
        m.db.session.flush()
        m.db.session.commit()
        return unit

    def attribute_unit(self):
        unit = m.ProductUnit()
        unit.code = fake.unique_str()
        unit.name = fake.text()

        m.db.session.add(unit)
        m.db.session.flush()
        m.db.session.commit()
        return unit
