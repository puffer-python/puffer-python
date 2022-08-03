# coding=utf-8
import random

import pytest

from catalog import models
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.validators.sellable import UpdateEditingStatusValidator
from catalog.api.product.sellable.schema import UpdateEditingStatusRequestBody


class UpdateStatusValidatorTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-563'
    FOLDER = 'SellableProduct/Update/Status'

    def cloneSellableSku(self):
        if not hasattr(self, 'sellables'):
            self.sellables = []
        self.sellables.append(fake.sellable_product(
            variant_id=self.variant.id,
            seller_sku=fake.text(),
            editing_status_code='processing',
            seller_id=self.user.seller_id,
            description=fake.text(),
            detailed_description=fake.text(),
            attribute_set_id=self.attribute_set.id,
        ))

    def run_validator(self):
        seller_id = self.data.pop('seller_id', None)
        data = UpdateEditingStatusRequestBody().load(self.data)
        UpdateEditingStatusValidator.validate({
            'seller_id': seller_id,
            **data
        })

    def setUp(self):
        fake.init_editing_status()

        self.attribute_set = fake.attribute_set()
        self.attribute_group = fake.attribute_group(self.attribute_set.id)

        self.user = fake.iam_user()
        self.product = fake.product(
            editing_status_code='processing',
            attribute_set_id=self.attribute_set.id,
        )
        self.variant = fake.product_variant(
            product_id=self.product.id,
            editing_status_code='processing'
        )
        self.sellable = fake.sellable_product(
            variant_id=self.variant.id,
            editing_status_code='processing',
            seller_id=self.user.seller_id,
            description=fake.text(),
            detailed_description=fake.text(),
            attribute_set_id=self.attribute_set.id,
        )
        self.image = fake.variant_product_image(self.variant.id)
        self.required_attr = fake.attribute(
            variant_id=self.variant.id,
            group_ids=[self.attribute_group.id],
            is_required=1
        )
        fake.attribute(
            variant_id=self.variant.id,
            group_ids=[self.attribute_group.id],
            is_required=0
        )
        self.data = {
            'seller_id': self.user.seller_id,
            'ids': [self.sellable.id],
            'status': 'pending_approval'
        }

    def test_passValiddata__passDataToService(self):
        self.run_validator()

    def test_passSellableIdOwnedByOtherSeller__raiseBadRequestException(self):
        self.data['ids'] = [fake.sellable_product(
            variant_id=self.variant.id,
            seller_id=fake.seller().id
        ).id]
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Cập nhật trạng thái biên tập của sản phẩm không tồn tại trên hệ thống'

    def test_passSellableWithoutDetailedDescription__raiseBadRequestException(self):
        self.sellable.terminal_seo.description = ''
        models.db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == f'Sản phẩm {self.sellable.name} thiếu mô tả đặc điểm chi tiết'

    def test_passSellableWithoutImage__raiseBadRequestException(self):
        models.db.session.delete(self.image)
        models.db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == f'Sản phẩm {self.sellable.name} cần có ít nhất 1 hình ảnh'

    def test_inactiveBundleItem__raiseBadRequestException(self):
        child = fake.sellable_product(
            variant_id=self.variant.id,
            editing_status_code='active',
            seller_id=self.user.seller_id,
            description=fake.text(),
            detailed_description=fake.text(),
            attribute_set_id=self.attribute_set.id,
        )
        fake.bundle(self.sellable, [child])
        self.data['ids'] = [child.id]
        self.data['status'] = 'inactive'
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == f'SKU đang thuộc sản phẩm bundle {self.sellable.name}. Vui lòng gỡ sku ra khỏi bundle trước khi vô hiệu'

    def test_check_multiple_message(self):
        self.sellable.terminal_seo.description = ''
        models.db.session.delete(self.image)
        models.db.session.commit()
        self.cloneSellableSku()
        self.data['ids'].append(random.choice(self.sellables).id)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert '\n' in error_info.value.message
