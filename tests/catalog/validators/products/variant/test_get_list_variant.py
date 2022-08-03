# coding=utf-8

import pytest

from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from catalog.validators.variant import GetListVariantValidator


class GetListGenericVariantTestCase(APITestCase):
    ISSUE_KEY = 'SC-389'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.product = fake.product(created_by=self.user.email)
        self.data = {}

    def run_validator(self):
        with logged_in_user(self.user):
            GetListVariantValidator.validate(self.data)

    def test_passProductOwned__returnValid(self):
        self.data['product_id'] = self.product.id
        self.run_validator()

    def test_passDraftProductOwnedByOtherUser__returnValid(self):
        p = fake.product(created_by=fake.iam_user().id, editing_status_code='draft')
        self.data['product_id'] = p.id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == f'Không tồn tại sản phẩm có id là {p.id}'

    def test_passPublishedProductOwnedByOtherUser__returnValid(self):
        p = fake.product(created_by=fake.iam_user().id, editing_status_code='approved')
        self.data['product_id'] = p.id
        self.run_validator()
