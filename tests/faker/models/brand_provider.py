# coding=utf-8
import logging
import random

import faker.providers
import os

import config
from catalog import models as m
from tests.faker import fake

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class BrandProvider(faker.providers.BaseProvider):
    """
    Cung cấp dữ liệu liên quan tới thương hiệu sản phẩm
    """
    def brand(self, name=None, code=None, is_active=1, internal_code=None, hasLogo=True):
        brand = m.Brand()
        code = code or fake.unique_str(8).lower()
        brand.code = code
        brand.internal_code = internal_code or f'TH{str(random.randint(1, 10000)).zfill(6)}'
        brand.name = name or fake.text()
        brand.is_active = 1 if is_active is None else is_active

        if hasLogo:
            brand.path = os.path.join(
                config.MEDIA_BRAND_DIR,
                code[0],
                f'{code}.png'
            )

        m.db.session.add(brand)
        m.db.session.flush()

        return brand
