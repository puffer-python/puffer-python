# coding=utf-8

from tests import logged_in_user
from tests.catalog.api import APITestCase
from marshmallow.validate import ValidationError
import pytest
from tests.faker import fake
from catalog.extensions import exceptions as exc
from catalog.validators.products import ProductCommonValidator
from catalog.api.product.product import schema


class CreateProductCommonTestCase(APITestCase):
    # ISSUE_KEY = 'SC-340'
    ISSUE_KEY = 'SC-550'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.category = fake.category(seller_id=self.seller.id, is_active=True)
        self.attribute_set = fake.attribute_set()
        self.tax = fake.tax()
        self.product = fake.product()
        self.data = {
            'name': fake.name(),
            'isBundle': False,
            'masterCategoryId': fake.master_category(is_active=True).id,
            'categoryId': self.category.id,
            'attributeSetId': self.attribute_set.id,
            'taxInCode': self.tax.code,
            'taxOutCode': self.tax.code,
            'brandId': fake.brand(is_active=True).id,
            'warrantyMonths': fake.integer(),
            'warrantyNote': fake.text(),
            'type': fake.misc(data_type='product_type', code=fake.text(5)).code,
            'unitId': fake.unit().id,
            'model': fake.text(),
            'detailedDescription': fake.text(),
            'description': fake.text()
        }

    def run_validator(self):
        with logged_in_user(self.user):
            data = schema.ProductCreateRequestBody().load(self.data)
            ProductCommonValidator.validate(data)

    def test_passValidaData__passTest(self):
        self.run_validator()

    def test_passNameTooLong__raiseValidationError(self):
        self.data['name'] = 'a' * 266
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passNameExisted__raiseBadRequestException(self):
        """
        Update validate
        Allow creating with the name been duplicated
        Remove raise Exception
        Jira ticket CATALOGUE-302
        """
        self.data['name'] = fake.product().name
        self.run_validator()

    def test_passNameContainSpecialChar__pass(self):
        self.data['name'] = fake.name() + '@#$%'
        self.run_validator()

    def test_missingRequireField__raiseValidationError(self):
        data = dict(self.data)
        self.data.pop('name')
        with pytest.raises(ValidationError):
            self.run_validator()
        self.data = dict(data)
        self.data.pop('brandId')
        with pytest.raises(exc.BadRequestException):
            self.run_validator()
        self.data = dict(data)
        self.data.pop('categoryId')
        with pytest.raises(exc.BadRequestException):
            self.run_validator()
        self.data = dict(data)
        self.data.pop('warrantyMonths')
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passBrandInactive__raiseBadRequestException(self):
        self.data['brandId'] = fake.brand(is_active=False).id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Thương hiệu đang bị vô hiệu, vui lòng chọn lại'

    def test_passBrandNotExist__raiseBadRequestException(self):
        self.data['brandId'] = fake.random_int(min=1000)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Thương hiệu không tồn tại, vui lòng chọn lại'

    def test_passMasterCategoryInactive__raiseBadRequestException(self):
        self.data['masterCategoryId'] = fake.master_category(is_active=False).id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục sản phẩm đang bị vô hiệu, vui lòng chọn lại'

    def test_passMasterCategoryHasActiveChildren__raiseBadRequestException(self):
        parent_master_category = fake.master_category(is_active=True)
        fake.master_category(parent_id=parent_master_category.id, is_active=True)
        self.data['masterCategoryId'] = parent_master_category.id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Vui lòng chọn danh mục sản phẩm là nút lá'

    def test_passMasterCategoryHasAllInactiveChildren__raiseBadRequestException(self):
        parent_master_category = fake.master_category(is_active=True)
        fake.master_category(parent_id=parent_master_category.id, is_active=False)
        self.data['masterCategoryId'] = parent_master_category.id
        self.run_validator()

    def test_passMasterCategoryNotExist__raiseBadRequestException(self):
        self.data['masterCategoryId'] = fake.random_int(1000)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục sản phẩm không tồn tại trên hệ thống, vui lòng chọn lại'

    def test_passUnitIdNotExist__raiseBadRequestException(self):
        self.data['unitId'] = fake.random_int(min=1000)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Đơn vị không tồn tại'

    def test_passModelTooLong__raiseValidationError(self):
        self.data['model'] = 'a' * 256
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passDescriptionTooLong__raiseValidationError(self):
        self.data['description'] = 'a' * 501
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passDetailedDescriptionTooLong__raiseValidationError(self):
        self.data['detailedDescription'] = 'a' * 70001
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passNameUpperCaseExisted__raiseValidatorError(self):
        """
        Update validate
        Allow creating with the name been duplicated
        Remove raise Exception
        Jira ticket CATALOGUE-302
        """
        self.data['name'] = self.product.name.upper()
        self.run_validator()


class CreateProductCommonTestCase2(CreateProductCommonTestCase):
    ISSUE_KEY = 'SC-380'

    def setUp(self):
        super().setUp()

    def test_missingRequireField__raiseValidationError(self):
        data = self.data
        super().test_missingRequireField__raiseValidationError()
        self.data = dict(data)
        self.data.pop('taxInCode')
        with pytest.raises(ValidationError):
            self.run_validator()
        self.data.pop('attributeSetId')
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passWarrantyNoteTooLong__raiseValidationError(self):
        self.data['warrantyNote'] = 'a' * 256
        with pytest.raises(ValidationError):
            self.run_validator()

    def test_passCategoryInActive__raiseBadRequestException(self):
        self.data['categoryId'] = fake.category(is_active=False, seller_id=self.user.seller_id).id
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Danh mục ngành hàng đang bị vô hiệu, vui lòng chọn lại'

    def test_passCategoryNotLeaf__raiseBadRequestException(self):
        fake.category(parent_id=self.category.id, is_active=True)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Vui lòng chọn danh mục ngành hàng là nút lá'

    def test_taxInNotExist__raiseBadRequestException(self):
        self.data['taxInCode'] = fake.text()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Mã thuế vào không tồn tại'

    def test_taxOutNotExist__raiseBadRequestException(self):
        self.data['taxOutCode'] = fake.text()
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Mã thuế ra không tồn tại'

    def test_passAttributeSetNotExist__raiseBadRequestException(self):
        self.data['attributeSetId'] = fake.random_int(1000)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Bộ thuộc tính không tồn tại'

    def test_passTypeNotExist__raiseBadRequestException(self):
        self.data['type'] = fake.text(6)
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Không tồn tại mã loại hình sản phẩm'

    def test_passBundleIsFalseAndNotTaxCode__raiseBadRequestException(self):
        self.data['isBundle'] = False
        self.data.pop('taxInCode')
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Vui lòng bổ sung Thuế mua vào'

    def test_passBundleIsTrueAndTaxCode__raiseBadRequestException(self):
        self.data['isBundle'] = True
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == 'Không nhập mã thuế vào đối với sản phẩm bundle'

    def test_passBundleIsTrueWithoutTaxCode__passValidator(self):
        self.data['isBundle'] = True
        self.data.pop('taxInCode')
        self.data.pop('taxOutCode')
        self.run_validator()

    def test_passValidDataAndExistedDraftProduct__raiseBadRequestException(self):
        p = fake.product(created_by=self.user.email, editing_status_code='draft')
        with pytest.raises(exc.BadRequestException) as error_info:
            self.run_validator()
        assert error_info.value.message == f'Bạn có 1 sản phẩm {p.name} ở seller {p.category.seller.name} đang trong quá trình tạo, vui lòng hoàn thành tạo mới sản phẩm đó để tiếp tục'
