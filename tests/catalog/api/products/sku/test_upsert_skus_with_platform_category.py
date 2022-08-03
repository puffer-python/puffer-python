# coding=utf-8
# pylint: disable=E0401
import random
from sqlalchemy import func

from catalog import models as m
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests.faker.models.category_provider import gen_path


class TestUpsertSku(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1130'
    FOLDER = '/Sku/UpsertSku/PlatformCategory'

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

    def setUp(self):
        self.created_by = 'quanglm'
        self.master_category = fake.master_category(is_active=True)
        self.category = fake.category(master_category_id=self.master_category.id, is_active=True)
        self.brand = fake.brand()
        self.tax = fake.tax(code="10")
        self.skus = []

    def _add_product_category(self, product, category):
        product_category = m.ProductCategory()
        product_category.product_id = product.id
        product_category.category_id = category.id
        product_category.created_by = self.created_by
        product_category.attribute_set_id = product.attribute_set_id
        m.db.session.add(product_category)
        m.db.session.commit()

    def _init_attribute_set(self):
        self.attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(
            set_id=self.attribute_set.id,
            system_group=False
        )
        self.attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        self.attribute_options = [
            fake.attribute_option(self.attributes[0].id, value='Vàng'),
            fake.attribute_option(self.attributes[0].id, value='Đỏ'),
            fake.attribute_option(self.attributes[1].id, value='S'),
            fake.attribute_option(self.attributes[1].id, value='XXL'),
        ]

        fake.attribute_group_attribute(
            attribute_id=self.attributes[0].id,
            group_ids=[attribute_group.id],
            is_variation=1
        )
        fake.attribute_group_attribute(
            attribute_id=self.attributes[1].id,
            group_ids=[attribute_group.id],
            is_variation=1
        )

    def _init_uom(self):
        self.uom_attribute_group = fake.attribute_group(
            set_id=self.attribute_set.id,
            system_group=True
        )
        self.uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[self.uom_attribute_group.id],
            is_variation=1
        )
        self.uom_ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[self.uom_attribute_group.id],
            is_variation=1
        )
        self.uom_attr_options = [
            fake.attribute_option(self.uom_attribute.id, value='Cái'),
            fake.attribute_option(self.uom_attribute.id, value='Chiếc')
        ]
        self.ratio_attr_options = [
            fake.attribute_option(self.uom_ratio_attribute.id, value='1'),
            fake.attribute_option(self.uom_ratio_attribute.id, value='2')
        ]

    def _init_products(self, update=True):
        if update:
            self.product = fake.product(
                category_id=self.category.id,
                master_category_id=self.master_category.id,
                created_by=self.created_by,
                attribute_set_id=self.attribute_set.id)
            self._add_product_category(self.product, self.category)
            self.payload = {
                'productId': self.product.id,
            }
        else:
            self.payload = {
                'taxInCode': self.tax.code,
                'productName': fake.text(),
                'brandId': self.brand.id,
                'providerId': 2,
                'masterCategoryId': self.master_category.id,
                'model': fake.text(),
                'warrantyMonths': fake.integer(max=12)
            }
        self.payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'attributeSetId': self.attribute_set.id,
            **self.payload
        }

    def _init_variants(self):
        self.payload_variants = []
        for index in range(2):
            for index_2 in range(len(self.uom_attr_options)):
                variant_2 = {
                    'uomId': self.uom_attr_options[index_2].id,
                    'uomRatio': self.ratio_attr_options[index_2].value,
                    'attributes': [{
                        'id': self.attributes[0].id,
                        'value': str(self.attribute_options[index].id)
                    }, {
                        'id': self.attributes[1].id,
                        'value': str(self.attribute_options[index + 2].id)
                    }]
                }
                self.payload_variants.append(variant_2)

    def _init_skus(self):
        for variant in self.payload_variants:
            variant['sku'] = {
                'images': [],
                'trackingType': False,
                'expiryTracking': False,
                'daysBeforeExpLock': fake.integer(),
                'productType': random.choice(['product', 'consu']),
                'sellerSku': fake.text()
            }

    def _init_payload(self, update_product=True, category_ids=None, category_id=None):
        self.payload = {}
        self._init_attribute_set()
        self._init_uom()
        self._init_products(update=update_product)
        self._init_variants()
        self._init_skus()

        self.payload = {
            **self.payload,
            'variants': self.payload_variants
        }

        if category_ids:
            self.payload['categoryIds'] = category_ids
        if category_id:
            self.payload['categoryId'] = category_id
        return self.payload

    def _equal_platform_category(self, category_id=None, product_id=None):
        product_id = product_id or self.product.id
        category_id = category_id or self.category.id
        product_category = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id,
                                                          m.ProductCategory.category_id == category_id).first()
        self.assertIsNotNone(product_category)

    def _get_not_existed_category_id(self):
        max_id = m.db.session.query(func.max(m.Category.id)).scalar() or 0
        return max_id + 1000

    def test_create_sku_return400_missing_both_category_id_and_category_ids_when_create(self):
        self._init_payload(update_product=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Vui lòng chọn danh mục ngành hàng', body['message'])

    def test_upsert_sku_return400_category_id_not_existed(self):
        self._init_payload(update_product=False, category_id=self._get_not_existed_category_id())
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Danh mục ngành hàng không tồn tại trên hệ thống, vui lòng chọn lại', body['message'])

    def test_upsert_sku_return400_category_ids_contain_id_not_existed(self):
        self._init_payload(update_product=False, category_ids=[self.category.id, self._get_not_existed_category_id()])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Danh mục ngành hàng không tồn tại trên hệ thống, vui lòng chọn lại', body['message'])

    def test_upsert_sku_return400_category_ids_contain_id_not_active(self):
        self.category.is_active = 0
        m.db.session.commit()
        self._init_payload(update_product=False, category_ids=[self.category.id])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Danh mục ngành hàng đang bị vô hiệu, vui lòng chọn lại', body['message'])

    def test_upsert_sku_return400_category_ids_duplicate_in_payload(self):
        self._init_payload(update_product=False, category_ids=[self.category.id, self.category.id])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Một sản phẩm chỉ được thuộc 1 danh mục ngành hàng của 1 seller', body['message'])

    def test_upsert_sku_return400_category_ids_duplicate_on_same_seller(self):
        new_category_on_same_seller = fake.category(seller_id=self.category.seller_id,
                                                    master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=False, category_ids=[self.category.id, new_category_on_same_seller.id])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Một sản phẩm chỉ được thuộc 1 danh mục ngành hàng của 1 seller', body['message'])

    def test_create_product_return200_with_only_category_id_in_payload(self):
        new_category = fake.category(seller_id=self.category.seller_id,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=False, category_id=new_category.id)
        new_category.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_id = body['result']['productId']
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id).all()
        self.assertEqual(200, code)
        self._equal_platform_category(new_category.id, product_id)
        self.assertEqual(1, len(product_categories))

    def test_create_product_return200_with_only_category_ids_in_payload(self):
        new_category = fake.category(seller_id=self.category.seller_id + 1,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=False, category_ids=[new_category.id, self.category.id])
        new_category.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_id = body['result']['productId']
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == product_id).all()
        self.assertEqual(200, code)
        self._equal_platform_category(product_id=product_id)
        self._equal_platform_category(category_id=new_category.id, product_id=product_id)
        self.assertEqual(2, len(product_categories))

    def test_update_product_return200_with_only_category_id_in_payload_existed_category_on_platform(self):
        new_category = fake.category(seller_id=self.category.seller_id,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_id=new_category.id)
        new_category.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == self.product.id).all()
        self.assertEqual(200, code)
        self._equal_platform_category(category_id=new_category.id)
        self.assertEqual(1, len(product_categories))

    def test_update_product_return200_with_only_category_id_in_payload_not_existed_category_on_platform(self):
        new_category = fake.category(seller_id=self.category.seller_id + 1,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_id=new_category.id)
        new_category.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == self.product.id).all()
        self.assertEqual(200, code)
        self._equal_platform_category()
        self._equal_platform_category(category_id=new_category.id)
        self.assertEqual(2, len(product_categories))

    def test_create_sku_return200_with_only_category_ids_in_payload_all_existed_category_on_platform(self):
        new_category = fake.category(seller_id=self.category.seller_id + 1,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_ids=[new_category.id, self.category.id])
        new_category.attribute_set_id = self.attribute_set.id
        self._add_product_category(self.product, new_category)
        code, body = self.call_api(self.payload)
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == self.product.id).all()
        self.assertEqual(200, code)
        self._equal_platform_category()
        self._equal_platform_category(category_id=new_category.id)
        self.assertEqual(2, len(product_categories))

    def test_update_product_return200_with_only_category_ids_in_payload_all_not_existed_category_on_platform(self):
        new_category1 = fake.category(seller_id=self.category.seller_id + 1,
                                      master_category_id=self.master_category.id, is_active=True)
        new_category2 = fake.category(seller_id=self.category.seller_id + 2,
                                      master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_ids=[new_category1.id, new_category2.id])
        new_category1.attribute_set_id = self.attribute_set.id
        new_category2.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == self.product.id).all()
        self.assertEqual(200, code)
        self._equal_platform_category()
        self._equal_platform_category(category_id=new_category1.id)
        self._equal_platform_category(category_id=new_category2.id)
        self.assertEqual(3, len(product_categories))

    def test_update_product_return200_with_only_category_ids_in_payload_has_existed_and_not_existed_category_on_platform(
            self):
        new_category = fake.category(seller_id=self.category.seller_id + 1,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_ids=[new_category.id, self.category.id])
        new_category.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == self.product.id).all()
        self.assertEqual(200, code)
        self._equal_platform_category()
        self._equal_platform_category(category_id=new_category.id)
        self.assertEqual(2, len(product_categories))

    def test_update_product_return200_with_category_ids_and_category_id_in_payload_only_category_ids_affect(self):
        new_category = fake.category(seller_id=self.category.seller_id + 1,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_ids=[new_category.id, self.category.id])
        new_category.attribute_set_id = self.attribute_set.id
        code, body = self.call_api(self.payload)
        product_categories = m.ProductCategory.query.filter(m.ProductCategory.product_id == self.product.id).all()
        self.assertEqual(200, code)
        self._equal_platform_category()
        self._equal_platform_category(category_id=new_category.id)
        self.assertEqual(2, len(product_categories))


class TestUpdateCategoryWithAttributeSet(TestUpsertSku):
    ISSUE_KEY = 'CATALOGUE-1356'
    FOLDER = '/Product/Update'

    def _create_sku(self):
        new_category = fake.category(seller_id=self.category.seller_id,
                                     master_category_id=self.master_category.id, is_active=True)
        self._init_payload(update_product=True, category_id=new_category.id)
        return self.call_api(self.payload)

    def test_default_attribute_set_of_category(self):
        category = fake.category()
        self.assertEqual(category.default_attribute_set.id, category.attribute_set_id)
        category.attribute_set_id = None
        m.db.session.commit()
        self.assertIsNone(category.default_attribute_set)
        parent_category = fake.category()
        category = fake.category(parent_id=parent_category.id)
        category.attribute_set_id = None
        m.db.session.commit()
        self.assertEqual(category.default_attribute_set.id, parent_category.attribute_set.id)

    def test_update_category(self):
        _, sku = self._create_sku()
        for index, _ in enumerate(self.payload.get('variants')):
            self.payload['variants'][index]['sku']['sku'] = sku['result']['variants'][index]['sku']
            self.payload['variants'][index]['variantId'] = sku['result']['variants'][index]['variantId']
            self.payload['variants'][index].pop('attributes')
        new_category = fake.category()
        self.payload.update({'categoryId': new_category.id})
        status, body = self.call_api(self.payload)
        self.assertEqual(status, 200)

    def test_update_category_non_attribute_set(self):
        _, sku = self._create_sku()
        for index, _ in enumerate(self.payload.get('variants')):
            self.payload['variants'][index]['sku']['sku'] = sku['result']['variants'][index]['sku']
            self.payload['variants'][index]['variantId'] = sku['result']['variants'][index]['variantId']
            self.payload['variants'][index].pop('attributes')
        new_category = fake.category()
        new_category.attribute_set_id = None
        new_category.parent_id = None
        new_category.path = gen_path(new_category)
        m.db.session.commit()
        self.payload.update({'categoryId': new_category.id})
        status, body = self.call_api(self.payload)
        self.assertEqual(status, 400)
        self.assertEqual(body.get('message'), 'Không thể cập nhật sang Danh mục không có Bộ thuộc tính')

    def test_update_category_attribute_set(self):
        _, sku = self._create_sku()
        for index, _ in enumerate(self.payload.get('variants')):
            self.payload['variants'][index]['sku']['sku'] = sku['result']['variants'][index]['sku']
            self.payload['variants'][index]['variantId'] = sku['result']['variants'][index]['variantId']
            self.payload['variants'][index].pop('attributes')

        attribute_set = fake.attribute_set()
        new_category = fake.category(attribute_set_id=attribute_set.id)
        self.payload.update({'categoryId': new_category.id})
        status, body = self.call_api(self.payload)
        self.assertEqual(status, 200)

    def test_update_category_same_attribute_set(self):
        _, sku = self._create_sku()
        for index, _ in enumerate(self.payload.get('variants')):
            self.payload['variants'][index]['sku']['sku'] = sku['result']['variants'][index]['sku']
            self.payload['variants'][index]['variantId'] = sku['result']['variants'][index]['variantId']
            self.payload['variants'][index].pop('attributes')

        new_category = fake.category(attribute_set_id=self.payload.get('attributeSetId'))
        self.payload.update({'categoryId': new_category.id})
        status, body = self.call_api(self.payload)
        self.assertEqual(status, 200)
