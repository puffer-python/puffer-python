# coding=utf-8
import logging
import faker.providers
from catalog.models import (
    db,
    SellableProductTag)
from tests.faker import fake

__author__ = 'Minh.ND'
_logger = logging.getLogger(__name__)


class SellableProductTagProvider(faker.providers.BaseProvider):
    """
    Cung cấp dữ liệu liên quan đến sản phẩm
    """

    def sellable_product_tag(self, sellable_product_id=None, sku=None, tags=None, **kwargs):
        ret = SellableProductTag()
        ret.sellable_product_id = sellable_product_id or fake.integer()
        ret.sku = sku or fake.text()
        ret.tags = tags or fake.text()
        ret.created_by = kwargs.get('created_by') or fake.iam_user().email
        ret.updated_by = kwargs.get('updated_by') or fake.iam_user().email

        db.session.add(ret)
        db.session.flush()

        return ret
