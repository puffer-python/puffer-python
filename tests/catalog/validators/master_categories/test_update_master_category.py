#coding=utf-8

from unittest import TestCase
import pytest
from marshmallow import ValidationError

from catalog.extensions import exceptions as exc
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests.utils import JiraTest
from catalog.api.master_category.schema import UpdateMasterCategoryRequest
from catalog.validators.master_category import UpdateMasterCategoryValidator


class UpdateMasterCategoryTestCase(APITestCase, JiraTest):
    ISSUE_KEY = 'SC-660'

    def setUp(self):
        self.category = fake.master_category()
        self.data = {
            'name': fake.name(),
            'code': fake.lexify(),
            'parentId': 0,
            'taxInCode': fake.tax().code,
            'taxOutCode': fake.tax().code,
            'attributeSetId': fake.attribute_set().id,
            'manageSerial': fake.boolean(),
            'image': fake.url() + '/lmao.png'
        }
        if self.data['manageSerial']:
            self.data['autoGenerateSerial'] = fake.boolean()

    def run_validator(self):
        data = UpdateMasterCategoryRequest().load(self.data)
        UpdateMasterCategoryValidator.validate({
            'cat_id': self.category.id,
            **data
        })

    def test_passValidData__passValidate(self):
        self.run_validator()

    def test_passSelfName__passValidate(self):
        self.data['name'] = self.category.name
        self.run_validator()

    def test_passSelfCode__passValidate(self):
        self.data['code'] = self.category.code
        self.run_validator()

    def test_taxCodeInvalid__raiseBadRequestException(self):
        self.data['taxInCode'] = self.data['taxInCode'] + fake.text()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Mã thuế vào không tồn tại'

    def test_attributeSetInvalid__raiseBadRequestException(self):
        self.data['attributeSetId'] = self.data['attributeSetId'] + 1
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Bộ thuộc tính không tồn tại'

    def test_parentIdNotExist__raiseBadRequestException(self):
        self.data['parentId'] = fake.random_int(10)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục cha không tồn tại trong hệ thống'

    def test_parentIdInactive__raiseBadRequestException(self):
        self.data['parentId'] = fake.master_category(is_active=False).id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Không thể tạo danh mục con cho danh mục vô hiệu'

    def test_nameVn__passValidate(self):
        self.data['name'] = 'Lmao tiếng việt'
        self.run_validator()

    def test_codeValid__passValidate(self):
        self.data['code'] = 'asdasd021321-_.'
        self.run_validator()

    # def test_dontPassManageSerial__raiseBadRequestException(self):
    #     self.data.pop('manageSerial')
    #     self.data['autoGenerateSerial'] = fake.boolean()
    #     with pytest.raises(exc.BadRequestException) as error_info:
    #         self.run_validator()
    #     error_info.value.message == 'Phải kích hoạt quản lí serial trước khi thiết lập tự động sinh serial'

    # def test_passManageSerialWithoutAutoGenerateSerial__raiseBadRequestException(self):
    #     self.data.pop('autoGenerateSerial', None)
    #     with pytest.raises(exc.BadRequestException) as error_info:
    #         self.run_validator()
    #     assert error_info.value.message == 'Thiếu tự động sinh serial'
