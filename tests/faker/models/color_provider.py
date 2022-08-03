# coding=utf-8
import logging
import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class ColorProvider(faker.providers.BaseProvider):
    def color(self):
        color = m.Color()
        color.code = fake.unique_str(6)
        color.name = fake.text()

        m.db.session.add(color)
        m.db.session.flush()

        return color
