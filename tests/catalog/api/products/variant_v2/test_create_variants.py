import logging
import config
from mock import patch
from sqlalchemy import func
import random
from tests.catalog.api import APITestCase
from catalog import constants, models as m
from tests.faker import fake

_author_ = 'Quang.LM'
_logger_ = logging.getLogger(__name__)


class MockResponseObject:
    def __init__(self, data, status_code):
        self.data = data
        self.status_code = status_code
        self.headers = {
            'Content-Type': 'image/jpeg',
            'Content-Length': 1024 * 1024
        }


class TestCreateListVariants(APITestCase):
    ISSUE_KEY = 'CATALOGUE-793'
    FOLDER = 'SkuList/Variants/Create'

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

    def setUp(self):
        self.created_by = 'quanglm'
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.product = fake.product(category_id=self.category.id,
                                    master_category_id=self.master_category.id,
                                    created_by=self.created_by)
        self.product_category = fake.product_category(product_id=self.product.id,
                                                      category_id=self.category.id)
        self.group = fake.attribute_group(self.product.attribute_set_id)
        self.attribute_uom = fake.attribute(code=constants.UOM_CODE_ATTRIBUTE)
        self.attribute_ratio = fake.attribute(code=constants.UOM_RATIO_CODE_ATTRIBUTE)
        self.variant_attributes = [fake.attribute(value_type='selection') for _ in range(5)]
        self.options = [fake.attribute_option(attribute.id) for attribute in self.variant_attributes]
        self.uom_option = fake.attribute_option(self.attribute_uom.id)
        self.uom_attributes = [self.attribute_uom, self.attribute_ratio]
        self.attribute_group_attribute = [fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[self.group.id],
            is_variation=True
        ) for attr in self.variant_attributes]
        for attr in self.uom_attributes:
            fake.attribute_group_attribute(
                attribute_id=attr.id,
                group_ids=[self.group.id],
                is_variation=True
            )

    def __init_payload(self, uom_option_id=None, uom_ratio=1.0, make_same=False, number_attributes=None):
        variants = []
        n = number_attributes or fake.random_int(2, 5)
        for _ in range(n):
            attributes = []
            for attr in self.attribute_group_attribute:
                attributes.append({
                    'id': attr.attribute_id,
                    'value': str(attr.attribute.options[0].id) if make_same
                    else str(fake.random_element(attr.attribute.options).id)
                })
            variants.append({
                'uomId': uom_option_id,
                'uomRatio': uom_ratio,
                'attributes': attributes
            })
        return {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'productId': self.product.id,
            'attributeSetId': self.product.attribute_set_id,
            'variants': variants
        }

    def __add_more_non_variant_attribute(self, payload, remove_uom=False):
        number_attr = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.NUMBER)
        text_attr = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.TEXT)
        select_attr = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.SELECTION)
        multi_attr = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.MULTIPLE_SELECT)

        for attr in [number_attr, text_attr, select_attr, multi_attr]:
            fake.attribute_group_attribute(
                attribute_id=attr.id,
                group_ids=[self.group.id],
                is_variation=False
            )

        option = fake.attribute_option(select_attr.id)
        options = [fake.attribute_option(multi_attr.id) for _ in range(3)]
        new_variants = []
        for v in payload['variants']:
            attributes  = v.get('attributes') or []
            attributes.append({'id': number_attr.id, 'value': str(fake.integer(max=1000000))})
            attributes.append({'id': text_attr.id, 'value': fake.text(20)})
            attributes.append({'id': select_attr.id, 'value': str(option.id)})
            attributes.append({'id': multi_attr.id, 'value': str.join(',', map(lambda x: str(x.id), options))})
            item = {'attributes': attributes}
            if not remove_uom:
                item = {'uomId': v.get('uomId'),
                        'uomRatio': v.get('uomRatio'),
                        'attributes': attributes}
            if v.get('variantId'):
                item['variantId'] = v.get('variantId')
            new_variants.append(item)
        payload['variants'] = new_variants

    def __get_not_found_option_id(self):
        max_id = m.db.session.query(func.max(m.AttributeOption.id)).first()[0] or 0
        return max_id + 1

    def test_return200__create_success_with_same_variant_attributes_but_uom_id(self):
        uom_option_id = self.uom_option.id
        more_option = fake.attribute_option(self.attribute_uom.id)
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=2)
        payload['variants'][0]['uomId'] = more_option.id
        payload['variants'][0]['uomRatio'] = random.randint(2, 1000)
        self.__add_more_non_variant_attribute(payload)
        code, body = self.call_api(payload)
        self.assertEqual(200, code)
        self.assertEqual(self.product.id, body['result']['productId'])
        self.assertEqual(2, len(body['result']['variants']))
        for v in body['result']['variants']:
            number_variant_attributes = m.VariantAttribute.query.filter(
                m.VariantAttribute.variant_id == v.get('variantId')).count()
            self.assertEqual(11, number_variant_attributes)

    def test_return200__create_success_with_same_uom_but_only_one_variant_attribute(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=2)
        more_option = fake.attribute_option(payload['variants'][0]['attributes'][0]['id'])
        payload['variants'][0]['attributes'][0]['value'] = str(more_option.id)
        self.__add_more_non_variant_attribute(payload)
        code, body = self.call_api(payload)
        self.assertEqual(200, code)
        self.assertEqual(self.product.id, body['result']['productId'])
        self.assertEqual(2, len(body['result']['variants']))
        for v in body['result']['variants']:
            number_variant_attributes = m.VariantAttribute.query.filter(
                m.VariantAttribute.variant_id == v.get('variantId')).count()
            self.assertEqual(11, number_variant_attributes)

    @patch('catalog.validators.variant.requests.get')
    def test_return200__update_success_non_variant_attributes(self, mock_response):
        response = MockResponseObject(None, 200)
        mock_response.return_value = response
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=2)
        more_option = fake.attribute_option(payload['variants'][0]['attributes'][0]['id'])
        payload['variants'][0]['attributes'][0]['value'] = str(more_option.id)
        code, body = self.call_api(payload)
        self.assertEqual(200, code)
        payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'productId': self.product.id,
            'attributeSetId': self.product.attribute_set_id,
            'variants': [{'variantId': body['result']['variants'][0].get('variantId')},
                         {'variantId': body['result']['variants'][1].get('variantId')}]
        }
        self.__add_more_non_variant_attribute(payload, remove_uom=True)
        code, body = self.call_api(payload)
        self.assertEqual(200, code, body)
        self.assertEqual(self.product.id, body['result']['productId'])
        self.assertEqual(2, len(body['result']['variants']))
        for v in body['result']['variants']:
            number_variant_attributes = m.VariantAttribute.query.filter(
                m.VariantAttribute.variant_id == v.get('variantId')).count()
            self.assertEqual(11, number_variant_attributes)

    def test_return400__missing_uom_id(self):
        payload = self.__init_payload()
        code, body = self.call_api(payload)
        field = body['result'][0]['field']
        message = body['result'][0]['message']
        self.assertEqual(400, code)
        self.assertEqual('uomId', field)
        self.assertIn('Field may not be null.', message)

    def test_return400__uom_id_not_found(self):
        uom_option_id = self.uom_option.id + 1
        payload = self.__init_payload(uom_option_id=uom_option_id)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Đơn vị tính không tồn tại', body['message'])

    def test_return400__uom_ratio_not_positive(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, uom_ratio=-0.1)
        code, body = self.call_api(payload)
        field = body['result'][0]['field']
        message = body['result'][0]['message']
        self.assertEqual(400, code)
        self.assertEqual('variants', field)
        self.assertTrue('-0.1 is not a positive value.' in str(message))

    def test_return400__missing_attributes_id(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id)
        payload['variants'][0]['attributes'][0]['id'] = None
        code, body = self.call_api(payload)
        field = body['result'][0]['field']
        message = body['result'][0]['message']
        self.assertEqual(400, code)
        self.assertEqual('variants', field)
        self.assertTrue('attributes' in str(message))
        self.assertTrue("attributes': {'0': {'id': ['Field may not be null." in str(message))

    def test_return400__attributes_id_not_integer(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id)
        payload['variants'][0]['attributes'][0]['id'] = 1.1
        code, body = self.call_api(payload)
        field = body['result'][0]['field']
        message = body['result'][0]['message']
        self.assertEqual(400, code)
        self.assertEqual('variants', field)
        self.assertTrue('attributes' in str(message))
        self.assertTrue('Not a valid integer.' in str(message))

    def test_return400__not_found_attributes_id(self):
        not_found_attr_id = max(map(lambda x: x.id, self.variant_attributes)) + 1
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id)
        payload['variants'][0]['attributes'][0]['id'] = not_found_attr_id
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Thuộc tính không tồn tại hoặc không thuộc bộ thuộc tính được chọn', body['message'])

    def test_return400__missing_variant_attributes_value(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, number_attributes=1)
        payload['variants'][0]['attributes'][0]['value'] = None
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Giá trị không tồn tại trên hệ thống', body['message'])

    def test_return400__attributes_value_exceed_255_with_text_type(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, number_attributes=1)
        payload['variants'][0]['attributes'][0]['value'] = fake.text(256)
        code, body = self.call_api(payload)
        field = body['result'][0]['field']
        message = body['result'][0]['message']
        self.assertEqual(400, code)
        self.assertEqual('variants', field)
        self.assertTrue('attributes' in str(message))
        self.assertTrue("{'attributes': {'0': {'value': ['Length must be between 0 and 255." in str(message))

    def test_return400__attributes_value_not_number_with_number_type(self):
        number_attribute = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.NUMBER)
        fake.attribute_group_attribute(
            attribute_id=number_attribute.id,
            group_ids=[self.group.id],
            is_variation=False
        )
        m.db.session.commit()
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, number_attributes=1)
        payload['variants'][0]['attributes'].append({'id': number_attribute.id, 'value': 'a'})
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Giá trị thuộc tính không phải là kiểu số', body['message'])

    def test_return400__attributes_is_select_value_not_an_option_id(self):
        not_found_option_id = self.__get_not_found_option_id()
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, number_attributes=1)
        payload['variants'][0]['attributes'][0]['value'] = str(not_found_option_id)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Giá trị không tồn tại trên hệ thống', body['message'])

    def test_return400__attributes_is_multi_select_value_not_an_option_id(self):
        multy_selection_attribute = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.MULTIPLE_SELECT)
        options = [fake.attribute_option(multy_selection_attribute.id) for _ in range(3)]
        fake.attribute_group_attribute(
            attribute_id=multy_selection_attribute.id,
            group_ids=[self.group.id],
            is_variation=False
        )
        value = str.join(',', map(lambda x: str(x.id), options))
        options.extend(self.options)
        not_found_option_id = self.__get_not_found_option_id()
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, number_attributes=1)
        payload['variants'][0]['attributes'][0]['value'] = f'{value},{not_found_option_id}'
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Giá trị không tồn tại trên hệ thống', body['message'])

    def test_return400__variant_attribute_not_in_attribute_set(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id)
        payload['variants'][0]['attributes'][0]['id'] = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.SELECTION).id
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Thuộc tính không tồn tại hoặc không thuộc bộ thuộc tính được chọn', body['message'])

    def test_return400__non_variant_attribute_not_in_attribute_set(self):
        number_attribute = fake.attribute(value_type=constants.ATTRIBUTE_TYPE.NUMBER)
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id)
        payload['variants'][0]['attributes'][0]['id'] = number_attribute.id
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Thuộc tính không tồn tại hoặc không thuộc bộ thuộc tính được chọn', body['message'])

    def test_return400__2_variants_with_same_attribute_values_and_uom_in_payload(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=2)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Tồn tại biến thể trùng lặp', body['message'])

    def test_return400__update_variant_attributes(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        payload['variants'][0]['variantId'] = body['result']['variants'][0].get('variantId')
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Không được phép cập nhật thuộc tính biến thể', body['message'])

    def test_return400__update_variant_not_found(self):
        payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'productId': self.product.id,
            'attributeSetId': self.product.attribute_set_id,
            'variants': [{'variantId': 1}]
        }
        self.__add_more_non_variant_attribute(payload, remove_uom=True)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Tồn tại biến thể không hợp lệ', body['message'])

    def test_return400__update_variant_but_no_product_id(self):
        payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'productName': fake.name(),
            'masterCategoryId': fake.master_category(is_active=True).id,
            'categoryId': fake.category(is_active=True, seller_id=self.category.seller_id).id,
            'brandId': fake.brand(is_active=True).id,
            'providerId': 1,
            'model': fake.text(),
            'taxInCode': fake.tax().code,
            'detailedDescription': fake.text(),
            'description': fake.text(),
            'warrantyMonths': fake.integer(),
            'attributeSetId': self.product.attribute_set_id,
            'variants': [{'variantId': 1}]
        }
        self.__add_more_non_variant_attribute(payload, remove_uom=True)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Không có thông tin sản phẩm khi cập nhật biến thể', body['message'])

    def test_return400__update_sku_but_no_variant_id(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=1)
        payload['variants'][0]['sku'] = {
            'sku': '123456',
            'images': [{
                'url': f'{config.BASE_IMAGE_URL}/abc',
                'altText': 'text'
            }]
        }
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Không có thông tin biến thể khi cập nhật sku', body['message'])

    def test_return400__exist_variants_with_same_attribute_values_and_uom_in_database(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        payload = self.__init_payload(uom_option_id=uom_option_id, uom_ratio=2, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        payload = self.__init_payload(uom_option_id=uom_option_id, uom_ratio=3, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể cùng loại có cùng đơn vị tính', body['message'])

    def test_return400__missing_base_uom_variant(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, uom_ratio=1.1, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Vui lòng nhập thông tin đơn vị tính cơ sở', body['message'])

    def test_return400__duplicate_base_uom_variant(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể có đơn vị tính cơ sở với ratio=1', body['message'])

    def test_return400__duplicate_not_base_uom_variant_with_same_uom(self):
        uom_option_id = self.uom_option.id
        payload = self.__init_payload(uom_option_id=uom_option_id, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        payload = self.__init_payload(uom_option_id=uom_option_id, uom_ratio=2, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        payload = self.__init_payload(uom_option_id=uom_option_id, uom_ratio=2, make_same=True, number_attributes=1)
        code, body = self.call_api(payload)
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể cùng loại có cùng đơn vị tính', body['message'])
