# coding=utf-8
import logging
import random
import faker.providers

from catalog import models as m
from tests.faker import fake

__author__ = 'Lam.NH'
_logger = logging.getLogger(__name__)


class LogProductEditProvider(faker.providers.BaseProvider):
    """
    Cung cấp dữ liệu liên quan đến lịch sử cập nhật sản phẩm
    """

    def log_product_edit(
            self,
            product_id=None,
            type=None,
            body=None,
            status=None,
            updated_by_email=None,
            updated_by_name=None
    ):
        product = m.LogEditProduct()
        product.product_id = product_id or 123
        product.type = type
        product.body = body or '12341412'
        product.status = status or fake.boolean()
        product.updated_by_email = updated_by_email or 'lam@gmail.com'
        product.updated_by_name = updated_by_name or 'lam'
        m.db.session.add(product)
        m.db.session.flush()

        return product
