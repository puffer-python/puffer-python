# coding=utf-8

import logging
from catalog import models

from catalog.services.categories import CategoryService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'thuc.tm'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()

class UpdateCategoryWithIsAdult(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1535'
    FOLDER = '/Category/UpdateCategoryWithIsAdult'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )
        self.parent_category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id
        )
        self.category = fake.category(
            seller_id = self.seller.id,
            parent_id = self.parent_category.id
        )

    def url(self, obj_id):
        return '/categories/{}'.format(obj_id)

    def update_method(self, data, id):
        with logged_in_user(self.user):
            return self.call_api(data=data, url=self.url(id))

    def check_body_return_400(self, body):
        assert body['code'] == 'INVALID'
        assert body['message'] == 'Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại'
        assert body['result'][0]['field'] == 'isAdult'

    def check_data_with_db(self, id, expected_is_adult):
        category_from_database = models.Category.query.filter(
            models.Category.id == id
        ).first()
        return category_from_database.is_adult == expected_is_adult

    def method(self):
        return 'PATCH'
    
    def test_update_is_adult_return_200_with_true_value(self):
        is_adult = True
        code, _ = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 200
        assert self.check_data_with_db(id=self.category.id, expected_is_adult=is_adult)

    def test_update_is_adult_return_200_with_false_value(self):
        is_adult = False
        code, _ = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 200
        assert self.check_data_with_db(id=self.category.id, expected_is_adult=is_adult)

    def test_update_is_adult_return_200_toggle_true_then_false(self):
        is_adult = True
        code, _ = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 200
        assert self.check_data_with_db(id=self.category.id, expected_is_adult=is_adult)

        is_adult = False
        code, _ = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 200
        assert self.check_data_with_db(id=self.category.id, expected_is_adult=is_adult)

    def test_update_is_adult_return_400_with_string_value(self):
        is_adult = fake.text(4)
        code, body = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 400
        self.check_body_return_400(body)

    def test_update_is_adult_return_400_with_number_value(self):
        is_adult = fake.integer(4)
        code, body = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 400
        self.check_body_return_400(body)
        
    def test_update_is_adult_return_400_with_float_value(self):
        is_adult = fake.float(4)
        code, body = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 400
        self.check_body_return_400(body)

    def test_update_is_adult_return_400_with_None_value(self):
        is_adult = None
        code, body = self.update_method(data={
            "isAdult": is_adult
        }, id=self.category.id)
        assert code == 400
        self.check_body_return_400(body)