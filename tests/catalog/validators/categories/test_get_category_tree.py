#coding=utf-8


import pytest

from catalog.extensions import exceptions as exc
from catalog.validators.category import GetCategoryTreeValidator
from catalog.services.categories import CategoryService
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user



class GetCategoryTreeTestCase(APITestCase):
    ISSUE_KEY = 'SC-395'

    def test_passCategoryIdNotExist__raiseBadRequestException(self):
        with logged_in_user(fake.iam_user()):
            with pytest.raises(exc.BadRequestException) as error_info:
                GetCategoryTreeValidator.validate({'category_id': fake.random_int()})
            assert error_info.value.message == 'Danh mục không tồn tại'

    def test_passCategoryInActive__raiseBadRequestException(self):
        user = fake.iam_user()
        with logged_in_user(user):
            category = fake.category(is_active=False, seller_id=user.seller_id)
            with pytest.raises(exc.BadRequestException) as error_info:
                GetCategoryTreeValidator.validate({'category_id': category.id})
            assert error_info.value.message == 'Danh mục đang vô hiệu'
