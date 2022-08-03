# coding=utf-8

from catalog import models
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.constants import ATTRIBUTE_TYPE


class UpdateVariantAttribute(APITestCase):
    ISSUE_KEY = 'CATALOGUE-932'
    FOLDER = '/Variant/Update'

    def setUp(self) -> None:
        self.sku = fake.sellable_product()
        self.iam_user = fake.iam_user()
        self.attribute = fake.attribute(value_type=ATTRIBUTE_TYPE.NUMBER)
        attribute_group = fake.attribute_group(set_id=self.sku.attribute_set_id)
        fake.attribute_group_attribute(group_ids=[attribute_group.id], attribute_id=self.attribute.id)
        models.db.session.commit()
        self.data = {
            'variants': [{
                'id': self.sku.product_variant.id,
                'attributes': [
                    {
                        'id': self.attribute.id,
                        'value': fake.text()
                    }
                ]
            }]
        }
        return

    def url(self):
        return '/variants/attributes'

    def method(self):
        return 'post'

    def test_attributeUnsigned_input0_successReturn200(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['attributes'][0]['value'] = 0
            self.attribute.is_unsigned = 0
            code, body = self.call_api(data=self.data)
            self.assertEqual(code, 200, body)

    def test_attributeUnsigned_inputGreaterThan0_successReturn200(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['attributes'][0]['value'] = fake.integer()
            self.attribute.is_unsigned = 1
            code, body = self.call_api(data=self.data)
            self.assertEqual(code, 200, body)

    def test_attributeUnsigned_inputLessThan0_invalidReturn400(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['attributes'][0]['value'] = fake.integer() * -1
            self.attribute.is_unsigned = 1
            code, body = self.call_api(data=self.data)
            self.assertEqual(code, 400, body)
            assert self.attribute.name in body.get('message')
            assert 'phải lớn lớn hơn 0' in body.get('message')

    def test_attributeNonUnsigned_inputLessThan0_successReturn200(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['attributes'][0]['value'] = fake.integer() * -1
            self.attribute.is_unsigned = 0
            code, body = self.call_api(data=self.data)
            self.assertEqual(code, 200, body)
