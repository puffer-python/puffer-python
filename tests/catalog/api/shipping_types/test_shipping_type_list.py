from catalog import models
import logging
import random

from sqlalchemy.sql.schema import ForeignKey

from tests.catalog.api import APITestCase

from tests.faker import fake
from tests.utils import PAGE_OUT_OF_RANGE, PAGE_SIZE_OUT_OF_RANGE

_author_ = 'phuong.h'
_logger_ = logging.getLogger(__name__)


class TestListShippingType(APITestCase):
    ISSUE_KEY = 'CATALOGUE-418'
    FOLDER = '/ShippingType/List'

    def url(self):
        return '/shipping_types'

    def method(self):
        return 'GET'

    def setUp(self):
        super().setUp()
        self.items = [fake.shipping_type() for _ in range(100)]
        self.page = 1
        self.page_size = 10

    def query_with(self, params):
        query_params = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        if 'page' not in params:
            query_params = f'{query_params}&page={self.page}'
        if 'pageSize' not in params:
            query_params = f'{query_params}&pageSize={self.page_size}'
        url = f'{self.url()}?{query_params}'

        code, body = self.call_api(url=url, method=self.method())

        return (code, body['result']['shippingTypes']) if code == 200 else (code, body)

    def test_return200__returnExactShippingTypeWithNameInQuery(self):
        item = random.choice(self.items)
        code, results = self.query_with({
            'name': item.name
        })

        self.assertEqual(200, code)
        self.assertEqual(item.id, results[0]['id'])
        self.assertEqual(item.code, results[0]['code'])
        self.assertEqual(item.name, results[0]['name'])

    def test_return200__returnExactShippingTypeWithCodeInQuery(self):
        item = random.choice(self.items)
        code, results = self.query_with({
            'name': item.name
        })

        self.assertEqual(200, code)
        self.assertEqual(item.id, results[0]['id'])
        self.assertEqual(item.code, results[0]['code'])
        self.assertEqual(item.name, results[0]['name'])

    def test_return200__returnNothing(self):
        code, items = self.query_with({
            'name': 'Tên này không tồn tại'
        })

        self.assertEqual(200, code)
        self.assertEqual(0, len(items))

    def test_return200__returnCorrectNumberOfItems(self):
        # run 100 times for accurate
        for i in range(1, 100):
            page = random.randint(1, 20)
            page_size = random.randint(1, 20)
            offset = (page - 1) * page_size
            remain = len(self.items) - offset
            expect_return = remain
            if remain < -1:
                expect_return = 0
            elif remain > page_size:
                expect_return = page_size

            code, items = self.query_with({
                'page': page,
                'pageSize': page_size
            })
            self.assertEqual(200, code)
            self.assertEqual(expect_return, len(items))

    def test_return400__pageOutOfRange(self):
        code, _ = self.query_with({'page': PAGE_OUT_OF_RANGE})
        self.assertEqual(400, code)

    def test_return400__pageNegative(self):
        code, _ = self.query_with({'page': -1})
        self.assertEqual(400, code)

    def test_return200__notPassingPageParam(self):
        # page default is 1 if absent
        code, _ = self.query_with({'pageSize': 20})
        self.assertEqual(200, code)

    def test_return400__pageEqualsZero(self):
        code, _ = self.query_with({'page': 0})
        self.assertEqual(400, code)

    def test_return400__pageSizeOutOfRange(self):
        code, _ = self.query_with({'pageSize': PAGE_SIZE_OUT_OF_RANGE})
        self.assertEqual(400, code)

    def test_return400__pageSizeNegative(self):
        code, _ = self.query_with({'pageSize': -1})
        self.assertEqual(400, code)

    def test_return200__notPassingPageSizeParam(self):
        # pageSize default is 10 if absent
        code, _ = self.query_with({'page': 1})
        self.assertEqual(200, code)

    def test_return400__pageSizeEqualsZero(self):
        code, _ = self.query_with({'pageSize': 0})
        self.assertEqual(400, code)

    def test_return200__correctOrderByIdDesc(self):
        sorted_lst = sorted(self.items, key=lambda k: k.is_default, reverse=True)
        # run 100 times for accurate
        for i in range(1, 100):
            page = random.randint(1, 20)
            page_size = random.randint(1, 20)
            offset = (page - 1) * page_size
            remain = len(self.items) - offset
            expect_return = remain
            if remain < -1:
                expect_return = 0
            elif remain > page_size:
                expect_return = page_size

            expected_items = []
            if expect_return > 0:
                expected_items = sorted_lst[offset:offset+expect_return:]

            code, items = self.query_with({
                'page': page,
                'pageSize': page_size
            })
            self.assertEqual(200, code)
            self.assertEqual(len(expected_items), len(items))
            for j in range(0, len(expected_items)):
                self.assertEqual(expected_items[j].id, items[j]['id'])

    def test_return200__returnWithCodeNameInQuery(self):
        item = random.choice(self.items)
        code, results = self.query_with({
            'name': item.name,
            'code': 'Không có ai ở đây đâu'
        })

        self.assertEqual(200, code)
        self.assertEqual(0, len(results))

        code, results = self.query_with({
            'name': item.name,
            'code': item.code
        })

        self.assertEqual(200, code)
        self.assertEqual(1, len(results))

    def test_return200__returnWithQueryInQuery(self):
        item = random.choice(self.items)
        code, results = self.query_with({
            'query': item.name
        })

        self.assertEqual(200, code)
        self.assertEqual(1, len(results))
        self.assertEqual(item.id, results[0]['id'])
        self.assertEqual(item.code, results[0]['code'])
        self.assertEqual(item.name, results[0]['name'])

        item = random.choice(self.items)
        code, results = self.query_with({
            'query': item.code
        })

        self.assertEqual(200, code)
        self.assertEqual(1, len(results))
        self.assertEqual(item.id, results[0]['id'])
        self.assertEqual(item.code, results[0]['code'])
        self.assertEqual(item.name, results[0]['name'])


class TestListShippingTypeDefault(APITestCase):
    ISSUE_KEY = 'CATALOGUE-666'
    FOLDER = '/ShippingType/List/Default'

    def url(self):
        return '/shipping_types'

    def method(self):
        return 'GET'

    def setUp(self):
        super().setUp()
        self.items = [fake.shipping_type() for _ in range(10)]
        self.page = 1
        self.page_size = 10

    def query_with(self, params):
        query_params = '&'.join(['%s=%s' % (k, v) for k, v in params.items()])
        if 'page' not in params:
            query_params = f'{query_params}&page={self.page}'
        if 'pageSize' not in params:
            query_params = f'{query_params}&pageSize={self.page_size}'
        url = f'{self.url()}?{query_params}'

        code, body = self.call_api(url=url, method=self.method())
        return (code, body['result']['shippingTypes']) if code == 200 else (code, body)

    def __set_default(self, shipping_type):
        shipping_type.is_default = True
        models.db.session.commit()

    def test_return200__with_no_default_shipping_type(self):
        code, shipping_types = self.query_with({'page': 1})

        self.assertEqual(200, code)
        for s in shipping_types:
            self.assertEqual(False, s['isDefault'])

    def test_return200__with_only_one_default_shipping_type(self):
        idx = random.randint(1, 9)
        default = self.items[idx]
        self.__set_default(default)

        code, shipping_types = self.query_with({'page': 1})

        self.assertEqual(200, code)
        self.assertEqual(True, shipping_types[0]['isDefault'])
