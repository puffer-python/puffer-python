import random
from unittest.mock import patch

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from urllib.parse import urlencode


class ImportHistoriesDetailItemsTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-404'
    FOLDER = '/Import/Histories/GetItems'

    def call_api(self, data=None, content_type=None, method=None, url=None):
        with logged_in_user(self.user):
            return super().call_api(data, content_type, method, url)

    def url(self):
        return '/import/histories/{}/items'.format(self.his_id)

    def method(self):
        return 'GET'

    def setUp(self):
        self.user = fake.iam_user()
        file_import = fake.file_import(user_info=self.user)
        [fake.result_import(file_import) for _ in range(3)]
        self.his_id = file_import.id
        self.patcher_seller = patch('catalog.services.seller.get_seller_by_id')
        self.mock_seller = self.patcher_seller.start()
        self.mock_seller.return_value = {
            'isAutoGeneratedSKU': False,
            'usingGoodsManagementModules': False
        }
        self.patcher_seller.start()

    def tearDown(self):
        super().tearDown()
        self.patcher_seller.stop()

    def testEmptyData_return200(self):
        code, body = self.call_api()
        assert code == 200
        self.assertEqual(body.get('code'), 'SUCCESS')

    def testCheckResultInResponse_return200(self):
        code, body = self.call_api()
        assert code == 200
        assert 'result' in body

    def testWithHistoryIdNotFound_return400(self):
        self.his_id = self.his_id + fake.id()
        code, body = self.call_api(
            url=self.url()
        )
        assert code == 400

    def testCheckCodeInResponse_return200(self):
        code, body = self.call_api()
        assert code == 200
        assert 'code' in body

    def testCheckMessageInResponse_return200(self):
        code, body = self.call_api()
        assert code == 200
        assert 'message' in body

    def testCheckPageSizeInQueryString_return200(self):
        page_size = fake.integer(max=1000000000)
        code, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({'pageSize': page_size})
        ))
        assert code == 200

    def testCheckPageSizeInvalidInQueryString_return400(self):
        page_size = 1000000000 + fake.integer()
        code, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({'pageSize': page_size})
        ))
        assert code == 400

    def testCheckPageInQueryString_return200(self):
        page = fake.integer(max=1000000000)
        code, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({'page': page})
        ))
        assert code == 200

    def testCheckPageInvalidInQueryString_return400(self):
        page_size = 1000000000 + fake.integer()
        code, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({'pageSize': page_size})
        ))
        assert code == 400

    def testCheckPaginationInResponse_return200(self):
        page_size = fake.integer(max=1000000000)
        page = fake.integer(max=1000000000)
        code, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({
                'pageSize': page_size,
                'page': page
            })
        ))
        assert code == 200
        assert body.get('result').get('currentPage') == page
        assert body.get('result').get('pageSize') == page_size

    def testCheckTotalRecordsInResponse_return200(self):
        from catalog.models import ResultImport
        total = ResultImport.query.filter(ResultImport.import_id == self.his_id).count()
        code, body = self.call_api()
        assert code == 200
        assert body.get('result').get('totalRecords') == total

    def testCheckItemsInResponse_return200(self):
        from catalog.models import ResultImport
        page_size = 10000 + fake.integer()
        total = ResultImport.query.filter(ResultImport.import_id == self.his_id).count()
        code, body = self.call_api(url='{}?{}'.format(self.url(), urlencode({'pageSize': page_size})))
        assert code == 200
        assert len(body.get('result').get('items') or []) == min(total, page_size)

    def testFilterStatusInvalid_return400(self):
        from catalog.models import ResultImport
        result_import = ResultImport.query.filter(
            ResultImport.import_id == self.his_id
        ).first()
        status = '{}{}'.format(result_import.status, fake.text())
        code, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({
                'status': status
            })
        ))
        assert code == 400

    def testFilterStatusValid_return200(self):
        from catalog.models import ResultImport
        result_import = ResultImport.query.filter(
            ResultImport.import_id == self.his_id
        ).first()
        code, body = self.call_api(
            url=self.url(),
            data={'status': result_import.status}
        )
        assert code == 200
        assert body.get('result', {}).get('items', {})[0].get('id') == result_import.id

    def testCheckMessageInDataResponse_return200(self):
        fake_message = fake.text()
        from catalog.models import ResultImport
        ResultImport.query.filter(
            ResultImport.import_id == self.his_id
        ).update(
            {ResultImport.message: fake_message}
        )
        _, body = self.call_api()

        item = random.choice(body.get('result', {}).get('items'))
        assert 'message' in item
        assert item.get('message') == fake_message

    def testCheckQueryInDataResponse_return200(self):
        fake_data = fake.text()
        from catalog.models import ResultImport
        result = ResultImport.query.filter(
            ResultImport.import_id == self.his_id
        ).first()

        result.data = '{}{}{}'.format(fake.text(), fake_data, fake.text())
        _, body = self.call_api(url='{}?{}'.format(
            self.url(),
            urlencode({
                'query': fake_data
            })
        ))

        item = random.choice(body.get('result', {}).get('items'))
        assert 'message' in item
        assert body['result']['items'][0].get('data') == result.data