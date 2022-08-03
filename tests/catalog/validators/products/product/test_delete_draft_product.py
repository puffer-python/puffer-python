#coding=utf-8

import pytest

from catalog.extensions import exceptions as exc
from catalog.validators.products import DeleteDraftProductValidator
from tests.faker import fake
from tests.catalog.api import APITestCase



class DeleteDraftProductTestCase(APITestCase):
    ISSUE_KEY = 'SC-447'

    def setUp(self):
        self.user = fake.iam_user()

    def run_validator(self):
        DeleteDraftProductValidator.validate({'email': self.user.email})

    def test_deleteProductHaveSku__raiseBadRequestException(self):
        product = fake.product(created_by=self.user.email, editing_status_code='draft')
        variant = fake.product_variant(product_id=product.id)
        image = fake.variant_product_image(variant.id)
        sku = fake.sellable_product(variant_id=variant.id)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Dữ liệu đang được sử dụng, bạn không thể xóa'

    def test_deleteProductDontHaveSku__returnSuccess(self):
        product = fake.product(created_by=self.user.email, editing_status_code='draft')
        variant = fake.product_variant(product_id=product.id)
        image = fake.variant_product_image(variant.id)
        self.run_validator()

    def test_deleteProductNotExist__returnSuccess(self):
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Bạn đang không có sản phẩm nháp'
