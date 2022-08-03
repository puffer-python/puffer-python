import logging
import random
from unittest.mock import patch

from catalog import models
from catalog.models import SellableProduct, Category, SellableProductShippingType, CategoryShippingType, db

from tests.catalog.api import APITestCase

from tests.faker import fake

_author_ = 'quang.lm'
_logger_ = logging.getLogger(__name__)


def get_map_sku_id_shipping_type(sku_ids):
    map_sku_id_shipping_type = {}
    for sku_id in sku_ids:
        map_sku_id_shipping_type[sku_id] = models.SellableProductShippingType.query.filter(
            SellableProductShippingType.sellable_product_id == sku_id).all()
    return map_sku_id_shipping_type


class TestAppendShippingTypeToSkus(APITestCase):
    ISSUE_KEY = 'CATALOGUE-479'
    FOLDER = '/Sellable/Apply/ShippingTypes'

    def url(self):
        return '/sellable_products/apply'

    def method(self):
        return 'POST'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.category_apply_shipping_type_to_sku_signal.send')

        self.mock_signal = self.patcher.start()
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )
        self.category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id
        )

    def init_payload(self, r_id, shipping_type_ids):
        return {
            'data': {
                'shippingType': {
                    'ids': shipping_type_ids,
                    'action': 'append'
                }
            },
            'filterCondition': {
                'categoryId': r_id
            }
        }

    def assert_success(self, r_id, shipping_type_ids):
        self.load_data_before_update(r_id, shipping_type_ids)
        code, body = self.call_api_with_login(data=self.init_payload(r_id, shipping_type_ids))
        self.assertEqual(code, 200, body)
        self.assert_match_in_db()
        return code, body

    def assert_fail(self, r_id, shipping_type_ids):
        code, body = self.call_api_with_login(data=self.init_payload(r_id, shipping_type_ids))
        self.assertEqual(code, 400)
        return code, body

    def load_data_before_update(self, category_id, shipping_type_ids):
        self.origin = {
            'category_id': category_id,
            'sku_ids': [],
            'map_sku_id_shipping_type': {},
            'shipping_type_ids': shipping_type_ids
        }

        categories = models.Category.query.all()
        descendant_category_ids = [category_id]
        i = 0
        while i < len(descendant_category_ids):
            c_id = descendant_category_ids[i]
            descendant_category_ids.extend(list(map(lambda x: x.id, filter(lambda x: x.parent_id == c_id, categories))))
            i = i+1

        # Get all sku belong to descendant categories
        self.origin['sku_ids'] = list(map(lambda x: x.id, db.session.query(SellableProduct.id).filter(
            SellableProduct.category_id.in_(descendant_category_ids)).all()))

        self.origin['map_sku_id_shipping_type'] = get_map_sku_id_shipping_type(self.origin['sku_ids'])

    def assert_merge_shipping_types(self, old, new, merge_ids, sku_id, category_id):

        old = [] if not old else old
        new = [] if not new else new
        assert merge_ids

        message = f'applied fail with sku_id={sku_id}, category_id={category_id} '

        for item in old:
            in_news = list(filter(lambda x: x.shipping_type_id == item.shipping_type_id, new))
            assert len(in_news) == 1, message
            in_new = in_news[0]
            assert item.id == in_new.id, message
            assert item.sellable_product_id == in_new.sellable_product_id, message
            assert item.shipping_type_id == in_new.shipping_type_id, message
            assert item.created_from == in_new.created_from, message
            assert item.updated_by == in_new.updated_by, message

        for item in merge_ids:
            if not any(filter(lambda x: x.shipping_type_id == item, old)):
                in_news = list(filter(lambda x: x.shipping_type_id == item, new))
                assert len(in_news) == 1, message
                in_new = in_news[0]
                assert sku_id == in_new.sellable_product_id, message
                assert item == in_new.shipping_type_id, message
                assert f'categories.id={category_id}' == in_new.created_from, message
                assert self.user.email == in_new.created_by, message
                assert self.user.email == in_new.updated_by, message

        assert not any(filter(lambda x:
                              not (any(filter(lambda y: y.shipping_type_id == x.shipping_type_id, old))
                                   or any(filter(lambda y: y == x.shipping_type_id, merge_ids))),
                              new)), message

    def assert_match_in_db(self):
        sku_ids = self.origin['sku_ids']
        new_map_sku_id_shipping_type = get_map_sku_id_shipping_type(sku_ids)
        for sku_id in sku_ids:
            self.assert_merge_shipping_types(
                old=self.origin['map_sku_id_shipping_type'][sku_id],
                new=new_map_sku_id_shipping_type[sku_id],
                merge_ids=self.origin['shipping_type_ids'],
                category_id=self.origin['category_id'],
                sku_id=sku_id
            )

    def init_shipping_types(self, n):
        ids = []
        for _ in range(0, n):
            ids.append(fake.shipping_type().id)
        return ids

    def test_return200__CategoryHasAShippingType(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(1)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__CategoryHasMultiShippingType(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(2)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__NoSku(self):
        self.test_return200__CategoryHasMultiShippingType()

    def test_return200__OneSku(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(3)
        fake.sellable_product(category_id=category_id)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__MultiSku(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(3)
        for _ in range(0, 5):
            fake.sellable_product(category_id=category_id)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__InactiveSku(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(3)
        for _ in range(0, 5):
            fake.sellable_product(category_id=category_id, editing_status_code='inactive')
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__SkuHasShippingType_DoNotBelongToCategory(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(3)
        for _ in range(0, 5):
            sellable_product = fake.sellable_product(category_id=category_id)
            for _ in range(1, 3):
                fake.sellable_product_shipping_type(sellable_product_id=sellable_product.id)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__SkuHasShippingType_AllBelongToCategory(self):
        category_id = self.category.id
        shipping_type_ids = self.init_shipping_types(3)
        for _ in range(0, 5):
            sellable_product = fake.sellable_product(category_id=category_id)
            for shipping_type_id in shipping_type_ids:
                if bool(random.getrandbits(1)):
                    fake.sellable_product_shipping_type(sellable_product_id=sellable_product.id,
                                                        shipping_type_id=shipping_type_id)
        self.assert_success(category_id, shipping_type_ids)

    @staticmethod
    def fake_complex_sku(category_id, shipping_type_ids):
        for _ in range(0, 5):
            sellable_product = fake.sellable_product(category_id=category_id)
            for shipping_type_id in shipping_type_ids:
                if bool(random.getrandbits(1)):
                    fake.sellable_product_shipping_type(sellable_product_id=sellable_product.id,
                                                        shipping_type_id=shipping_type_id)
            for _ in range(0, 3):
                fake.sellable_product_shipping_type(sellable_product_id=sellable_product.id)

    def test_return200__SkuHasShippingType_OneBelongAndOneDoNotBelongToCategory(self):
        shipping_type_ids = self.init_shipping_types(3)
        category_id = self.category.id
        self.fake_complex_sku(category_id, shipping_type_ids)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__InactiveCategory(self):
        shipping_type_ids = self.init_shipping_types(3)
        category = fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_category.id,
            is_active=False
        )
        category_id = category.id
        self.fake_complex_sku(category_id, shipping_type_ids)
        self.assert_success(category_id, shipping_type_ids)

    def test_return200__SkuOfChildCategory(self):
        shipping_type_ids = self.init_shipping_types(3)
        category_id = self.category.id
        for _ in range(0, 3):
            child_category = fake.category(
                seller_id=self.seller.id,
                master_category_id=self.master_category.id,
                parent_id=category_id)
            self.fake_complex_sku(child_category.id, shipping_type_ids)
            for _ in range(0, 2):
                grandchild_category = fake.category(
                    seller_id=self.seller.id,
                    master_category_id=self.master_category.id,
                    parent_id=child_category.id)
                self.fake_complex_sku(grandchild_category.id, shipping_type_ids)
        self.fake_complex_sku(category_id, shipping_type_ids)
        self.assert_success(category_id, shipping_type_ids)

    def test_return400__EmptyShippingTypeIds(self):
        category_id = self.category.id
        _, body = self.assert_fail(category_id, [])
        self.assertEqual(
            body['message'], f'Danh sách loại hình vận chuyển không được để trống', [])

    def test_return400__CategoryNotExists(self):
        shipping_type_ids = self.init_shipping_types(1)
        category_id = random.randint(10000, 1000000)
        _, body = self.assert_fail(category_id, shipping_type_ids)
        self.assertEqual(
            body['message'], f'Không tồn tại bản ghi có id = {category_id} trong bảng categories', shipping_type_ids)

    def test_return400__CategoryOfOtherSeller(self):
        shipping_type_ids = self.init_shipping_types(1)
        category = fake.category(
            seller_id=self.seller.id + 1,
            master_category_id=self.master_category.id)
        _, body = self.assert_fail(category.id, shipping_type_ids)
        self.assertEqual(body['message'], f'Bạn không quản lý ngành hàng này')

    def tearDown(self):
        self.patcher.stop()
