# coding=utf-8

import pytest
from marshmallow.validate import ValidationError
from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.api.product.variant import schema
from catalog.validators.variant import CreateVariantValidator
from catalog import models
from tests import logged_in_user


class ValidateCreateVariantDataTestCase(APITestCase):
    ISSUE_KEY = 'SC-341'

    def setUp(self):
        # setup database
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.group = fake.attribute_group(self.attribute_set.id)
        self.attribute_ratio = fake.attribute(code='uom_ratio')
        self.attribute_uom = fake.attribute(code='uom')
        self.attributes = [fake.attribute(value_type='selection') for _ in range(10)]
        self.options = [fake.attribute_option(attribute.id) for attribute in self.attributes]
        self.attribute_group_attribute = [fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[self.group.id],
            is_variation=True
        ) for attr in self.attributes]
        self.master_category = fake.master_category(
            is_active=True
        )
        self.category = fake.category(
            is_active=True,
            seller_id=self.seller.id,
        )
        self.product = fake.product(
            master_category_id=self.master_category.id,
            category_id=self.category.id,
            attribute_set_id=self.attribute_set.id,
            created_by=self.user.email
        )
        self.product_category = fake.product_category(
            product_id=self.product.id,
            category_id=self.category.id
        )

        # setup request data
        variants = list()
        existed_variants = {}
        for n_variant in range(fake.random_int(2, 5)):
            attributes = list()
            while True:
                for attr in self.attribute_group_attribute:
                    attr_data = {
                        'id': attr.attribute_id,
                        'value': fake.random_element(attr.attribute.options).id
                    }
                    attributes.append(attr_data)
                attr_key = str(attributes)
                if not existed_variants.get(attr_key):
                    existed_variants[attr_key] = 1
                    variants.append({
                        'attributes': attributes
                    })
                    break

        self.data = {
            'productId': self.product.id,
            'variants': variants
        }

    def run_validator(self):
        with logged_in_user(self.user):
            data = schema.CreateVariantsBodyRequest().load(self.data)
            CreateVariantValidator.validate({'data': data, 'seller_id': self.user.seller_id, 'created_by': self.user.email})

    def test_passValidData__passValidator(self):
        self.run_validator()

    def test_passProductNotExist__raiseBadRequestException(self):
        self.data['productId'] = self.product.id + 1
        with pytest.raises(exc.BadRequestException) as error:
            self.run_validator()
            assert error.value.message == 'Sản phẩm không tồn tại trên hệ thống'
        self.data['productId'] = self.product.id + 1

    def test_passUnVariationAttribute__raiseBadRequestException(self):
        attr = fake.attribute(value_type='selection')
        unvariantion_attr = fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[self.group.id],
            is_variation=False
        )
        self.data['variants'][0]['attributes'][0]['id'] = unvariantion_attr.attribute_id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()

    def test_passUnSelectionAttribute__raiseBadRequestException(self):
        attr = fake.attribute(value_type='multiple_select')
        multiple_select_attr = fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[self.group.id],
            is_variation=True
        )
        self.data['variants'][0]['attributes'][0]['id'] = multiple_select_attr.attribute_id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()

    def test_passAttributeOptionNotExist__raiseBadRequestException(self):  # TODO: lmao
        self.data['variants'][0]['attributes'][0]['value'] = fake.random_int(min=1000)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Giá trị không tồn tại trên hệ thống'

    @pytest.mark.skip(reason='@Todo')
    def test_passAttributeDontHaveOption__raiseBadRequestException(self):
        for option in self.options:
            if option.attribute_id != self.data['variants'][0]['attributes'][0]['id']:
                self.data['variants'][0]['attributes'][0]['value'] = option.id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Giá trị không thể gán cho thuộc tính'

    def test_raiseValidationError__whenMissingProductId(self):
        self.data.pop('productId')
        with pytest.raises(ValidationError) as error_info:
            self.run_validator()
        errors = error_info.value.messages
        assert 'productId' in errors

    def test_raiseValidationError__whenMissingAttributeId(self):
        self.data['variants'][0]['attributes'][0].pop('id')
        with pytest.raises(ValidationError) as error_info:
            self.run_validator()
        errors = error_info.value.messages
        assert 'variants' in errors

    def test_raiseValidationError__whenMissingAttributeValue(self):
        self.data['variants'][0]['attributes'][0].pop('value')
        with pytest.raises(ValidationError) as error_info:
            self.run_validator()
        errors = error_info.value.messages
        assert 'variants' in errors

    def test_createDefaultVariant_whenPassProductWithoutVariant(self):
        for item in self.attribute_group_attribute:
            item.is_variation = False
            models.db.session.add(item)
        models.db.session.commit()
        self.data.pop('variants')
        self.run_validator()

    def test_createDefaultVariant_whenPassProductHaveVariant(self):
        self.data.pop('variants')
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Sản phẩm bắt buộc phải có biến thể'

    def test_passProductWithInactiveMasterCategory_raiseBadRequestException(self):
        self.product.category.is_active = False
        models.db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục ngành hàng đang vô hiệu, không thể tạo biến thể'

    def test_passDuplicateAttribute_raiseBadRequestException(self):  # TODO: lmao 1
        self.data['variants'][0]['attributes'].append(self.data['variants'][0]['attributes'][0])
        self.data['variants'] = [self.data['variants'][0]]
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Trùng lặp dữ liệu'

    def test_passProductWithMasterCategoryNotLeaf_raiseBadRequestException(self):
        fake.category(parent_id=self.product.category.id, is_active=True)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        error_info.value.message == 'Danh mục ngành hàng phải là lá'

    def test_passProductWithMasterCategoryHaveLeafInactive_returnSuccess(self):  # TODO: lmao
        fake.master_category(parent_id=self.product.master_category.id, is_active=False)
        self.run_validator()

    def test_passProductHaveDefaultVariant_raiseBadRequestEcception(self):
        fake.product_variant(product_id=self.product.id)
        for item in self.attribute_group_attribute:
            item.is_variation = False
            models.db.session.add(item)
        models.db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        error_info.value.message == 'Sản phẩm đã tồn tại biến thể mặc định'

    @pytest.mark.skip(reason='Now we can set any category for a product')
    def test_passProductOwnedByOtherSeller_raiseBadRequestException(self):
        category = fake.category(seller_id=fake.seller().id)
        product = fake.product(
            created_by=self.user.email,
            category_id=category.id,
            attribute_set_id=self.attribute_set.id,
        )
        self.data['productId'] = product.id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        error_info.value.message == 'Sản phẩm không tồn tại trên hệ thống'
