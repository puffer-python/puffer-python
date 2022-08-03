# coding=utf-8

import pytest
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.validators.sellable import UpdateItemBundleValidator
from catalog.api.product.sellable import schema
from catalog.models import db


class UpdateItemBundleValidatorTestCase(APITestCase):
    ISSUE_KEY = 'SC-554'

    def setUp(self):
        self.user = fake.iam_user()
        seller_id = self.user.seller_id
        self.bundle = fake.sellable_product(
            seller_id=seller_id,
            editing_status_code='processing',
            is_bundle=True,
        )
        self.items = [
            fake.sellable_product(seller_id=seller_id,
                                  editing_status_code='processing',
                                  is_bundle=False),
            fake.sellable_product(seller_id=seller_id,
                                  editing_status_code='processing',
                                  is_bundle=False),
        ]
        self.data = {
            'items': [
                {
                    'id': self.items[0].id,
                    'quantity': fake.random_int(1,10)
                },
                {
                    'id': self.items[1].id,
                    'quantity': fake.random_int(1,10)
                }
            ]
        }

    def run_validator(self):
        data = schema.UpdateSellableBundleRequestBody().load(self.data)
        UpdateItemBundleValidator.validate({
            'sellable_id': self.bundle.id,
            'seller_id': self.user.seller_id,
            **data
        })

    def test_passValidData__passValidator(self):
        self.run_validator()

    def test_passBundleOwnedByOtherSeller__raiseBadRequestException(self):
        self.bundle = fake.sellable_product(seller_id=self.user.seller_id + 1)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Sản phẩm không tồn tại'

    def test_passSellableIsNotBundle__raiseBadRequestException(self):
        self.bundle.is_bundle = False
        db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Sản phẩm không phải sản phẩm bundle'

    def test_passEmptyItemsWhenBundleIsActive__raiseBadRequestException(self):
        self.bundle.editing_status_code = 'active'
        self.data['items'] = []
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Phải tồn tại ít nhất một sản phẩm'

    def test_passEmptyItemsWhenBundleIsNotActive__passValidator(self):
        self.bundle.editing_status_code = 'processing'
        self.data['items'] = []
        self.run_validator()

    def test_passDuplicateItem__raiseBadRequestException(self):
        self.data['items'].append(self.data['items'][0])
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Không được tồn tại 2 sản phẩm giống nhau'

    def test_passItemNotExist__raiseBadRequestException(self):
        self.data['items'][0]['id'] = fake.random_int(100, 1000)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại sản phẩm không hợp lệ'

    def test_passItemOwnedByOtherUser__raiseBadRequestException(self):
        self.items[0].seller_id = self.user.seller_id + 1
        db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại sản phẩm không hợp lệ'

    def test_passItemIsBundle__raiseBadRequestException(self):
        self.items[0].is_bundle = True
        db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại sản phẩm không hợp lệ'

    def test_passItemInactive__raiseBadRequestException(self):
        self.items[0].editing_status_code = 'inactive'
        db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại sản phẩm không hợp lệ'
