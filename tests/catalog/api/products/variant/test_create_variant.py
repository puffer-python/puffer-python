# coding=utf-8
import random

import pytest
import requests
from mock import patch

from catalog import models
from catalog.utils import decapitalize
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class CreateVariantAPITestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-497'

    def url(self):
        return '/variants'

    def method(self):
        return 'POST'

    def setUp(self):
        # setup database
        self.iam_user = fake.iam_user()
        self.attribute_set = fake.attribute_set()
        self.group = fake.attribute_group(self.attribute_set.id)
        self.attribute_ratio = fake.attribute(code='uom_ratio')
        self.attribute_uom = fake.attribute(code='uom')
        self.attributes = [fake.attribute(value_type='selection') for _ in range(15)]
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
            seller_id=self.iam_user.seller_id,
            is_active=True,
        )
        self.product = fake.product(
            master_category_id=self.master_category.id,
            category_id=self.category.id,
            attribute_set_id=self.attribute_set.id,
            created_by=self.iam_user.email
        )
        self.product_category = fake.product_category(
            product_id=self.product.id,
            category_id=self.category.id
        )

        # setup request data
        variants = list()
        for n_variant in range(fake.random_int(1, 5)):
            attributes = list()
            for attr in self.attribute_group_attribute:
                attributes.append({
                    'id': attr.attribute_id,
                    'value': fake.random_element(attr.attribute.options).id
                })
            variants.append({
                'attributes': attributes
            })
        self.data = {
            'productId': self.product.id,
            'variants': variants
        }

        self.patcher_seller = patch('catalog.services.seller.get_seller_by_id')
        self.mock_seller = self.patcher_seller.start()

    def tearDown(self):
        self.patcher_seller.stop()

    def test_returnSuccessResponse__whenPassValidator(self):
        with logged_in_user(self.iam_user):
            code, body = self.call_api(self.data)
            assert 200 == code
            assert 'SUCCESS' == body['code']
            assert self.product.id == body['result']['productId']
            assert len(self.data['variants']) == len(body['result']['variants'])

    def test_returnErrorResponse__whenUnPassValidator(self):
        with logged_in_user(self.iam_user):
            self.data['productId'] = fake.random_int(min=1000)
            code, body = self.call_api(self.data)
            assert 400 == code
            assert 'INVALID' == body['code']

    def test_createDefaultVariant_whenPassProductWithoutVariant(self):
        with logged_in_user(self.iam_user):
            for item in self.attribute_group_attribute:
                item.is_variation = False
                models.db.session.add(item)
            models.db.session.commit()
            self.data.pop('variants')
            code, body = self.call_api(self.data)
            assert 200 == code
            assert 'SUCCESS' == body['code']
            assert 1 == len(body['result']['variants'])


class MockResponse:
    def __init__(self, status_code, headers, data):
        self.status_code = status_code
        self.headers = headers
        self.data = data


class UpdateVariantImageAPITestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-532'
    FOLDER = '/Variants/Update'

    def url(self):
        return '/variants'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.product = fake.product()
        self.product_variant_1 = fake.product_variant(product_id=self.product.id)
        self.product_variant_2 = fake.product_variant(product_id=self.product.id)
        self.data = {
            "variants": [
                {
                    'id': self.product_variant_1.id,
                    'images': [
                        {
                            'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                        },
                        {
                            'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                        }
                    ]
                },
                {
                    'id': self.product_variant_2.id,
                    'images': [
                        {
                            'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                        },
                        {
                            'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                        },
                        {
                            'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                        }

                    ]
                },
            ]
        }
        self.iam_user = fake.iam_user()

    def test_returnListVariantImages_whenCreateSuccessfully(self):
        with logged_in_user(self.iam_user):
            product_variant_3 = fake.product_variant(product_id=1)
            data_product_3 = {
                'variants':
                    [
                        {
                            'id': product_variant_3.id,
                            'images':
                                [
                                    {
                                        'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                                    }
                                ]
                        }
                    ]
            }
            self.call_api(data_product_3)

            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)
            self.assertTrue(isinstance(body, dict))

            result = body.get('result').get('variants')

            self.assertEqual(len(result), 2)
            self.assertEqual(len(result[0].get('images')), 2)
            self.assertEqual(len(result[1].get('images')), 3)

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == product_variant_3.id
            ).order_by(
                models.VariantImage.priority.asc()
            ).all()

            self.assertEqual(len(images), 1)

            for data in self.data.get('variants'):
                images = models.VariantImage.query.filter(
                    models.VariantImage.product_variant_id == data.get('id')
                ).order_by(
                    models.VariantImage.priority.asc()
                ).all()

                priority_dict = {}
                for image in images:
                    self.assertIsNone(priority_dict.get(image.priority))
                    priority_dict[image.priority] = image.priority
                    self.assertIsNotNone(image.created_by)
                    self.assertIsNotNone(image.updated_by)

    def test_returnListVariantImages_whenDeleteSuccessfully(self):
        with logged_in_user(self.iam_user):
            self.call_api(self.data)

            self.data.get('variants')[0]['images'] = []
            self.data.get('variants')[1]['images'] = []

            code, body = self.call_api(self.data)

            self.assertEqual(code, 200)
            self.assertTrue(isinstance(body, dict))

            result = body.get('result').get('variants')

            self.assertEqual(len(result), 2)
            self.assertEqual(len(result[0].get('images')), 0)
            self.assertEqual(len(result[1].get('images')), 0)

            for data in self.data.get('variants'):
                images = models.VariantImage.query.filter(
                    models.VariantImage.product_variant_id == data.get('id')
                ).order_by(
                    models.VariantImage.priority.asc()
                ).all()

                self.assertEqual(len(images), 0)

    def test_returnListVariantImages_whenUpdateSuccessfully(self):
        with logged_in_user(self.iam_user):
            self.call_api(self.data)

            self.data.get('variants')[1]['id'] = self.product_variant_1.id
            del self.data.get('variants')[0]

            code, body = self.call_api(self.data)

            self.assertEqual(code, 200)
            self.assertTrue(isinstance(body, dict))

            result = body.get('result').get('variants')

            self.assertEqual(len(result), 1)
            self.assertEqual(len(result[0].get('images')), 3)

            images = models.VariantImage.query.filter(
                models.VariantImage.product_variant_id == self.product_variant_1.id
            ).order_by(
                models.VariantImage.priority.asc()
            ).all()

            priority_dict = {}
            for image in images:
                self.assertIsNone(priority_dict.get(image.priority))
                priority_dict[image.priority] = image.priority

    def test_notPassVariantImage_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            data = {
                "variants": [
                    {"id": 1}
                ]
            }

            code, body = self.call_api(data)
            self.assertEqual(code, 400)
            self.assertEqual(body.get('result')[0].get('message')['0']['images'], ["Missing data for required field."])

    def test_notPassInvalidVariants_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            data = {"variants": 1}

            code, body = self.call_api(data)
            self.assertEqual(code, 400)

            self.assertEqual(body.get('result')[0].get('message'), ["Invalid type."])

    def test_notPassVariantIdOfAProduct_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            product_variant_3 = fake.product_variant(product_id=fake.product().id)
            self.data.get('variants').append({
                'id': product_variant_3.id,
                'images': [
                    {
                        'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg',
                    },
                    {
                        'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                    }
                ]
            })

            code, body = self.call_api(self.data)

            self.assertEqual(code, 400)
            self.assertEqual(body.get('message'), 'Các biến thể không thuộc cùng 1 sản phẩm')

            for data in self.data.get('variants'):
                images = models.VariantImage.query.filter(
                    models.VariantImage.product_variant_id == data.get('id')
                ).order_by(
                    models.VariantImage.priority.asc()
                ).all()

                self.assertEqual(len(images), 0)

    def test_passEmptyPayload_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'] = []

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body.get('message'), 'Bạn cần cập nhật một thông tin nào đó')

    def test_passInvalidVariantId_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['id'] = 'abc'

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body.get('result')[0].get('message')['0']['id'], ["Not a valid integer."])

    def test_passNotExistVariantId_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['id'] = 99 + fake.integer()

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)

            self.assertEqual(body.get('message'), 'Biến thể không chính xác')

    def test_passImagesParamIsNotInstanceOfList_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = 'abc'
            self.data['variants'][1]['images'] = 'abc'

            code, body = self.call_api(self.data)

            self.assertEqual(code, 400)
            result = body.get('result')[0]
            self.assertEqual(result.get('message')['0']['images'], ["Invalid type."])
            self.assertEqual(result.get('message')['1']['images'], ["Invalid type."])

    def test_passImagesParamIsNotInstanceOfStringList_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg',
                123
            ]

            code, body = self.call_api(self.data)

            self.assertEqual(code, 400)

    def test_invalidTotalImage_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][1]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                }
                for _ in range(37)
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body.get('message'), 'Vượt quá giới hạn ảnh cho một biến thế (36 ảnh)')

    def test_passInvalidUrlImage_returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/bBt9dgd-lOqtjUy4KN2aXrkJ98Rtb_TuhZ-BGPhVM0DuESNMdu6qc9KIHybWiyTESwzp7281paRfu2OX-eg'
                },
                {
                    'url': 'https://storagse.googleapis.com/teko-gae.appspot.com/media/image/2020/3/30/20200330_2a9112dd-93ae-4424-be5d-dab896f5c2bd'
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)
            self.assertEqual(body.get('message'), 'Đường dẫn không hợp lệ')

    def test_passImageSmallerThan500x500__returnSuccessfully(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw'
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)

    def test_passEmptyPayload__returnBadRequest(self):
        with logged_in_user(self.iam_user):
            self.data = []

            code, body = self.call_api(self.data)

            self.assertEqual(code, 400)

    def testUpdateVariantWithMissingAltTextImage_200_success(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)

    def testUpdateVariantWithEmptyAltTextImage_200_success(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'altText': ''
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)

    def testUpdateVariantWithValidAltTextImage_200_success(self):
        with logged_in_user(self.iam_user):
            alt_text = fake.text()
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'altText': alt_text
                }
            ]

            code, body = self.call_api(self.data)
            body.get('result').get('variants')
            self.assertEqual(code, 200)

    def testUpdateVariantWithAltTextImage_Length255_200_success(self):
        with logged_in_user(self.iam_user):
            alt_text = fake.text(255)
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'altText': alt_text
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)
            self.assertEqual(body['result']['variants'][0]['images'][0]['altText'], alt_text)

    def testUpdateVariantWithAltTextImage_Over255_400_invalid(self):
        with logged_in_user(self.iam_user):
            alt_text = fake.text(255 + fake.integer())
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'altText': alt_text
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)

    def testUpdateVariantWithMissingAllowDisplayImage_200_success(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 200)

    def testUpdateVariantWithAllowDisplay_True_200_success(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'allowDisplay': True
                }
            ]

            code, body = self.call_api(self.data)
            self.assertTrue(body['result']['variants'][0]['images'][0]['allowDisplay'])
            self.assertEqual(code, 200)

    def testUpdateVariantWithAllowDisplay_False_200_success(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'allowDisplay': False
                }
            ]

            code, body = self.call_api(self.data)
            self.assertFalse(body['result']['variants'][0]['images'][0]['allowDisplay'])
            self.assertEqual(code, 200)

    def testUpdateVariantWithAllowDisplay_NotBoolean_400_invalid(self):
        with logged_in_user(self.iam_user):
            self.data['variants'][0]['images'] = [
                {
                    'url': 'https://lh3.googleusercontent.com/muvK80rOpzixF9Ii9djkmYgQUWxgymeDY6xkZ8fxNwnr5QC6xQBOkA8MYqq1AaiB-X6n0qppdg2qKXvPnw',
                    'allowDisplay': fake.text()
                }
            ]

            code, body = self.call_api(self.data)
            self.assertEqual(code, 400)
