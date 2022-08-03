import json
import logging

from tests.catalog.api import APITestCaseWithMysql
from catalog import models as m
from tests.faker import fake
from catalog.constants import RAM_QUEUE
from catalog.extensions.ram_queue_consumer import _get_category_seller_ids

_author_ = 'Quang.lm'
_logger_ = logging.getLogger(__name__)


class TestSyncSellingPlatform(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-1395'
    FOLDER = '/MasterData/Seller/Platform'

    def url(self):
        return '/master-data/selling-seller-platform'

    def method(self):
        return 'POST'

    def test_return400__with_empty_platform_id(self):
        data = {
            'sellerId': 1,
            'ownerSellerId': 2,
        }
        code, _ = self.call_api(data=data)
        self.assertEqual(400, code)

    def test_return400__with_empty_seller_id(self):
        data = {
            'platformId': 1,
            'ownerSellerId': 2,
        }
        code, _ = self.call_api(data=data)
        self.assertEqual(400, code)

    def test_return400__with_empty_owner_seller_id(self):
        data = {
            'platformId': 1,
            'sellerId': 2,
        }
        code, _ = self.call_api(data=data)
        self.assertEqual(400, code)

    def _assert_seller_platform(self, data):
        seller_platform = m.PlatformSellers.query.filter(m.PlatformSellers.seller_id == data.get('sellerId'),
                                                         m.PlatformSellers.platform_id == data.get(
                                                             'platformId')).first()
        is_default = False
        if data.get('isDefault'):
            is_default = True

        self.assertIsNotNone(seller_platform)
        self.assertEqual(is_default, seller_platform.is_default)
        seller_platform = m.PlatformSellers.query.filter(m.PlatformSellers.seller_id == data.get('ownerSellerId'),
                                                         m.PlatformSellers.platform_id == data.get(
                                                             'platformId')).first()

        self.assertIsNotNone(seller_platform)
        self.assertEqual(True, seller_platform.is_owner)

    def test_return200__success_with_not_default_platform(self):
        m.db.session.execute('truncate table ram_events')
        data = {
            'sellerId': 1,
            'platformId': 1,
            'ownerSellerId': 2,
            'isDefault': 0
        }
        code, _ = self.call_api(data=data)
        events = [r for r in m.db.session.execute('select * from ram_events')]

        self.assertEqual(200, code)
        self._assert_seller_platform(data)
        self.assertEqual(0, len(events))

    def test_return200__success_with_default_platform(self):
        m.db.session.execute('truncate table ram_events')
        data = {
            'sellerId': 1,
            'platformId': 1,
            'ownerSellerId': 1,
            'isDefault': 2
        }
        code, _ = self.call_api(data=data)
        events = [r for r in m.db.session.execute('select * from ram_events order by id')]

        self.assertEqual(200, code)
        self._assert_seller_platform(data)
        self.assertEqual(1, len(events))
        self.assertEqual(RAM_QUEUE.RAM_PLATFORM_SELLER_UPSERT_KEY, events[0]['key'])
        self.assertDictEqual({'seller_id': 1, 'platform_id': 1, 'owner_seller_id': 1}, json.loads(events[0]['payload']))

    def test_unit_get_correct_seller_id_with_seller_from_message(self):
        fake.platform_sellers(platform_id=1, seller_id=1, is_default=True, is_owner=True)
        fake.platform_sellers(platform_id=2, seller_id=1, is_default=False, is_owner=True)
        seller_ids = _get_category_seller_ids({'id': 1, 'seller_id': 2}, 1)
        self.assertListEqual([2], seller_ids)

    def test_unit_get_correct_seller_id_without_seller_from_message(self):
        m.db.session.execute('truncate table platform_sellers')
        fake.platform_sellers(platform_id=1, seller_id=1, is_default=True, is_owner=True)
        fake.platform_sellers(platform_id=2, seller_id=1, is_default=False, is_owner=True)
        fake.platform_sellers(platform_id=1, seller_id=2, is_default=True, is_owner=False)
        fake.platform_sellers(platform_id=1, seller_id=3, is_default=True, is_owner=False)
        fake.platform_sellers(platform_id=2, seller_id=4, is_default=True, is_owner=False)
        seller_ids = _get_category_seller_ids({'id': 1}, 1)
        self.assertListEqual([1, 2, 3, 4], seller_ids)
