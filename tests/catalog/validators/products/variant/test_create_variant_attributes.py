# coding=utf-8

import pytest
from mock import patch
from marshmallow import ValidationError

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.validators.variant import CreateVariantAttributeValidator
from catalog.api.product.variant import schema
from catalog import models
from catalog.extensions import exceptions as exc


class CreateVariantAttributeTestCase(APITestCase):
    ISSUE_KEY = 'SC-377'

    def setUp(self):
        # setup database
        self.iam_user = fake.iam_user()

        self.attribute_set = fake.attribute_set()
        self.groups = {
            'normal': fake.attribute_group(
                set_id=self.attribute_set.id,
                system_group=False
            ),
            'system': fake.attribute_group(
                set_id=self.attribute_set.id,
                system_group=True
            )
        }
        self.attributes = {
            'system': {
                'number': fake.attribute(value_type='number'),
            },
            'normal': {
                'text': fake.attribute(value_type='text'),
                'number': fake.attribute(value_type='number'),
                'selection': fake.attribute(value_type='selection'),
                'multiple_select': fake.attribute(value_type='multiple_select')
            }
        }
        self.options = [fake.attribute_option(self.attributes['normal']['selection'].id),
                        fake.attribute_option(self.attributes['normal']['multiple_select'].id),
                        fake.attribute_option(self.attributes['normal']['multiple_select'].id)]
        self.attribute_group_attribute = {
            'normal': [],
            'system': []
        }
        for attr in self.attributes['normal'].values():
            self.attribute_group_attribute['normal'].append(fake.attribute_group_attribute(
                attribute_id=attr.id,
                group_ids=[self.groups['normal'].id],
                is_variation=False
            ))
        self.master_category = fake.master_category(
            is_active=True
        )
        fake.master_category(parent_id=self.master_category.id, is_active=False)
        self.product = fake.product(
            master_category_id=self.master_category.id,
            attribute_set_id=self.attribute_set.id
        )
        # setup variants
        self.variation_attribute = fake.attribute(value_type='selection')
        self.variation_opts = [fake.attribute_option(self.variation_attribute.id),
                               fake.attribute_option(self.variation_attribute.id)]
        fake.attribute_group_attribute(
            attribute_id=self.variation_attribute.id,
            group_ids=[self.groups['normal'].id],
            is_variation=True
        )
        fake.attribute_group_attribute(
            attribute_id=self.variation_attribute.id,
            group_ids=[self.groups['normal'].id],
            is_variation=True
        )
        self.variants = [fake.product_variant(self.product.id, self.iam_user.email),
                         fake.product_variant(self.product.id, self.iam_user.email)]
        models.db.session.add(models.VariantAttribute(
            variant_id=self.variants[0].id,
            attribute_id=self.variation_attribute.id,
            value=str(self.variation_attribute.options[0].id)
        ))
        models.db.session.add(models.VariantAttribute(
            variant_id=self.variants[1].id,
            attribute_id=self.variation_attribute.id,
            value=str(self.variation_attribute.options[1].id)
        ))
        models.db.session.commit()

        # setup request data
        self.data = {
            'variants': []
        }
        for variant in self.variants:
            attributes = []
            attributes.append({
                'id': self.attributes['normal']['text'].id,
                'value': fake.text()
            })
            attributes.append({
                'id': self.attributes['normal']['number'].id,
                'value': fake.random_number()
            })
            attributes.append({
                'id': self.attributes['normal']['selection'].id,
                'value': fake.random_element(self.attributes['normal']['selection'].options).id
            })
            attributes.append({
                'id': self.attributes['normal']['multiple_select'].id,
                'value': list(map(
                    lambda option: option.id,
                    self.attributes['normal']['multiple_select'].options,
                ))
            })
            self.data['variants'].append({
                'id': variant.id,
                'attributes': attributes
            })
            self.params = {
                'filled': True
            }

    def run_validator(self):
        data = schema.CreateVariantAttributeRequest().load(self.data)
        validator = CreateVariantAttributeValidator()
        with logged_in_user(self.iam_user):
            return validator.validate({'data': data, 'seller_id': self.iam_user.seller_id, **self.params})

    def test_passValidData__returnSuccess(self):
        self.run_validator()

    def test_passNoneValue__returnSuccess(self):
        self.data['variants'][0]['attributes'][0]['value'] = None
        self.run_validator()

    def test_passValueIsDict__raiseValidationError(self):
        self.data['variants'][0]['attributes'][0]['value'] = dict()
        with pytest.raises(ValidationError) as e:
            self.run_validator()
        assert e.value.messages['variants'][0]['attributes'][0]['value'] == \
            ['Kiểu dữ liệu không hợp lệ']

    def test_passValueIsListString__raiseValidationError(self):
        self.data['variants'][0]['attributes'][0]['value'] = ['1']
        with pytest.raises(ValidationError) as e:
            self.run_validator()
        assert e.value.messages['variants'][0]['attributes'][0]['value'] == \
            ['Kiểu dữ liệu không hợp lệ']

    def test_passVariantsNotExist__raiseBadRequestException(self):
        self.data['variants'][0]['id'] = fake.random_int(min=100)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại biến thể không hợp lệ'

    def test_passVariantsNotBelongTogatherProduct__raiseBadRequestException(self):
        self.data['variants'][0]['id'] = fake.product_variant(
            fake.product().id, self.iam_user.email).id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Các biến thể phải cùng một sản phẩm'

    def test_passTextValueInvalidFormat__raiseBadRequestException(self):
        self.data['variants'][0]['attributes'][0]['value'] = 'a' * 256
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Giá trị text quá dài'

    def test_passNumberValueInvalidFormat__raiseBadRequestException(self):
        self.data['variants'][0]['attributes'][1]['value'] = 'string'
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Dữ liệu phải là kiểu số'

    def test_passSelectionValueInvalidFormat__raiseBadRequestException(self):
        self.data['variants'][0]['attributes'][2]['value'] = 'string'
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Giá trị phải là option id'

    def test_passMultipleSelectValueInvalidFormat__raiseBadRequestException(self):
        self.data['variants'][0]['attributes'][3]['value'] = 'str'
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Giá trị phải là danh sách các option id'

    def test_passOptionValueNotExist__raiseBadRequestException(self):
        self.data['variants'][0]['attributes'][2]['value'] = fake.random_int(100)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại giá trị không hợp lệ'

    def test_passOptionValueNotBelongAttribute__raiseBadRequestException(self):
        self.data['variants'][0]['attributes'][2]['value'] = \
            self.data['variants'][0]['attributes'][3]['value'][0]
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại giá trị không hợp lệ'

    def test_passVariantOwnOtherSeller__pass(self):
        other_seller = fake.seller()
        other_user = fake.user(seller_id=other_seller.id)
        other_variant = fake.product_variant(
            product_id=self.product.id,
            created_by=other_user.email
        )
        self.data['variants'][0]['id'] = other_variant.id
        self.run_validator()

    def test_passVariationDuplicateAttribute__raiseBadrequestException(self):
        self.data['variants'][0]['attributes'][0] = self.data['variants'][0]['attributes'][1]
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Tồn tại dữ liệu trùng lặp'

    def test_passProductOfNotLeafMasterCategory__raiseBadRequestException(self):
        fake.master_category(parent_id=self.product.master_category.id, is_active=True)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục của sản phẩm không phải danh mục lá'

    def test_passProductOfInactiveMasterCategory__raiseBadRequestException(self):
        self.product.master_category.is_active = False
        models.db.session.commit()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục của sản phẩm đang vô hiệu'
