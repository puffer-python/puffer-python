# coding=utf-8
import logging
import random

import faker.providers
import os

import config
from catalog import models as m
from tests.faker import fake

__author__ = 'phuong.h'
_logger = logging.getLogger(__name__)


class ShippingTypeProvider(faker.providers.BaseProvider):
    """
    Provide data to Shipping Type
    """
    def shipping_type(self, name=None, code=None, is_active=1, is_default=0):
        entity = m.ShippingType()
        code = code or fake.unique_str(255).upper()
        entity.code = code
        entity.name = name or fake.text(255)
        entity.is_active = 1 if is_active is None else is_active
        entity.is_default = 1 if is_default else 0
        m.db.session.add(entity)
        m.db.session.flush()

        return entity

