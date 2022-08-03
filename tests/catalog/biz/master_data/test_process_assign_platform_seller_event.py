import json
import logging
from datetime import datetime, timedelta

import requests
from mock import patch

import config
from catalog import models as m, constants
from catalog.constants import RAM_QUEUE
from catalog.extensions.ram_queue_consumer import process_platform_seller_upsert
from tests.catalog.api import APITestCaseWithMysql
from tests.faker import fake

_author_ = 'Quang.lm'
_logger_ = logging.getLogger(__name__)


class TestSyncSellingPlatformToSrm(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-1395'
    FOLDER = '/MasterData/Seller/Platform'

    def _create_categories(self, seller_id):
        cat1 = fake.category(seller_id=seller_id)
        cat21 = fake.category(seller_id=seller_id, parent_id=cat1.id)
        cat22 = fake.category(seller_id=seller_id, parent_id=cat1.id)
        cat211 = fake.category(seller_id=seller_id, parent_id=cat21.id)
        cat212 = fake.category(seller_id=seller_id, parent_id=cat21.id)
        cat221 = fake.category(seller_id=seller_id, parent_id=cat22.id)
        cat222 = fake.category(seller_id=seller_id, parent_id=cat22.id)
        self.categories = [cat1, cat21, cat22, cat211, cat212, cat221, cat222]

    @patch('requests.post')
    def test_not_sync_categories_to_srm_if_failed_sync_first_category(self, mock_request):
        resp = requests.Response()
        resp.status_code = 400
        resp._content = json.dumps({}).encode('utf-8')
        mock_request.return_value = resp
        data = {
            'seller_id': 1,
            'platform_id': 1,
            'owner_seller_id': 2
        }
        now = datetime.now()
        m.db.session.execute('truncate table ram_events')
        m.db.session.execute('truncate table categories')
        self._create_categories(2)
        process_platform_seller_upsert(json.dumps(data))
        events = [r for r in m.db.session.execute('select * from ram_events order by id')]
        self.assertEqual(1, len(events))
        self.assertEqual(RAM_QUEUE.RAM_PLATFORM_SELLER_UPSERT_KEY, events[0]['key'])
        self.assertGreaterEqual(events[0]['want_to_send_after'],
                                now + timedelta(seconds=config.SYNC_CATEGORY_TO_SRM_REPEAT_TIME))

    @patch('requests.post')
    def test_sync_categories_to_srm_if_successfully_sync_first_category(self, mock_request):
        resp = requests.Response()
        resp.status_code = 200
        resp._content = json.dumps({}).encode('utf-8')
        mock_request.return_value = resp
        data = {
            'seller_id': 1,
            'platform_id': 1,
            'owner_seller_id': 2
        }
        m.db.session.execute('truncate table ram_events')
        m.db.session.execute('truncate table categories')
        self._create_categories(2)
        process_platform_seller_upsert(json.dumps(data))
        events = [r for r in m.db.session.execute('select * from ram_events order by id')]
        self.assertEqual(len(self.categories), len(events))
        i = 0
        for cat in self.categories:
            even = events[i]
            i += 1
            payload = json.loads(even['payload'])
            self.assertEqual(RAM_QUEUE.RAM_INSERT_CATEGORY_KEY, even['key'])
            self.assertEqual(cat.id, payload.get('id'))
            self.assertEqual(data.get('seller_id'), payload.get('seller_id'))
