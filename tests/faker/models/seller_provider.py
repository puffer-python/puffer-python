# coding=utf-8
import logging

import faker.providers

from catalog.models import (
    db,
    Seller,
    Provider,
    PlatformSellers
)
from tests.faker import fake

__author__ = 'thiem.nv'
_logger = logging.getLogger(__name__)


class SellerProvider(faker.providers.BaseProvider):
    """
    Cung cấp dữ liệu liên quan tới Seller
    """

    def seller(self, manual_sku=True, is_manage_price=False, status=True):
        ret = Seller(name=fake.name())
        ret.manual_sku = manual_sku
        ret.is_manage_price = is_manage_price
        ret.code = fake.unique_str(len=4)
        ret.status = status
        db.session.add(ret)
        db.session.flush()

        return ret

    def seller_prov(self):
        prov = Provider()
        prov.name = fake.text()
        prov.display_name = fake.text()
        prov.code = fake.text(length=8)
        prov.is_active = True
        prov.created_by = fake.email()
        db.session.add(prov)
        db.session.flush()

        return prov

    def platform_sellers(self, seller_id, platform_id, is_default=False, is_owner=False):
        seller_platform = PlatformSellers()
        seller_platform.seller_id = seller_id
        seller_platform.platform_id = platform_id
        seller_platform.is_owner = is_owner
        seller_platform.is_default = is_default
        db.session.add(seller_platform)
        db.session.flush()
        return seller_platform
