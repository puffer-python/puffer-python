# coding=utf-8
import logging
import pytest

from tests import logged_in_user
from tests.catalog.validators import BaseValidatorTestCase
from tests.faker import fake
from tests.utils import JiraTest
from catalog.api.product.sellable import schema
from catalog.validators.sellable import UpdateSellableProductTerminalValidator
from catalog.extensions import exceptions as exc
from catalog.extensions.marshmallow import ValidationError

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class UpdateSellableProductTerminalValidatorTestCase(BaseValidatorTestCase, JiraTest):
    # ISSUE_KEY = 'SC-386'
    ISSUE_KEY = 'SC-655'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.sellable = fake.sellable_product()
        self.terminals = [fake.terminal(
            seller_id=self.seller.id,
            terminal_type='online'
        ) for _ in range(3)]

        self.data = {
            'skus': [self.sellable.sku],
            "sellerTerminals": [{
                "applySellerId": self.seller.id,
                "terminals": [{
                    "terminalType": "online",
                    "terminalCodes": [terminal.code for terminal in self.terminals]
                }]
            }]
        }
        self.declare_schema(schema.SellableProductTerminalSchema)
        self.invoke_validator(UpdateSellableProductTerminalValidator)

    def test_passInvalidSKU__raiseBadRequestException(self):
        self.data['skus'] = [123]
        with pytest.raises(ValidationError), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passSKUNotExist__raiseBadRequestException(self):
        self.data['skus'] = ["abcdefghjklmno"]
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passDuplicateSKU__raiseBadRequestException(self):
        self.data['skus'] = self.data['skus'] +  self.data['skus']
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passSKUNotBelongToSameProduct__raiseBadRequestException(self):
        sellable = fake.sellable_product()
        self.data['skus'].append(sellable.sku)
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passInactiveSKU__raiseBadRequestException(self):
        self.sellable.editing_status_code = 'inactive'
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passSellerNotExist__raiseBadRequestException(self):
        self.data['sellerTerminals'][0]['applySellerId'] = 69
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passSellerInvalid__raiseValidationError(self):
        self.data['sellerTerminals'][0]['applySellerId'] = "abc"
        with pytest.raises(ValidationError), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passTerminalTypeInvalid__raiseBadRequestException(self):
        self.data['sellerTerminals'][0]['terminals'][0]['terminalType'] = "abc"
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passTerminalCodesInvalid__raiseBadRequestException(self):
        self.data['sellerTerminals'][0]['terminals'][0]['terminalCodes'] = "abc"
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passTerminalCodeNotExist__raiseBadRequestException(self):
        self.data['sellerTerminals'][0]['terminals'][0]['terminalCodes'] = 69
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)

    def test_passDuplicateData__raiseBadRequestException(self):
        self.data['sellerTerminals'] = self.data['sellerTerminals'] + self.data['sellerTerminals']
        with pytest.raises(exc.BadRequestException), \
             logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            self.do_validate(self.data)
