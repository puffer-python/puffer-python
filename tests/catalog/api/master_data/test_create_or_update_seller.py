import datetime
import logging
import random

from catalog.models import Seller
from tests.catalog.api import APITestCase
from tests.faker import fake

_author_ = 'Nam.Vh'
_logger_ = logging.getLogger(__name__)


class TestCreateSeller(APITestCase):
    def url(self):
        return '/master-data/sellers'

    def method(self):
        return 'POST'

    def setUp(self):
        self.data = {
            'id': fake.integer(),
            'name': fake.name(),
            'code': fake.unique_str(len=4),
            'isActive': random.choice([True, False]),
            'isAutoGeneratedSku': random.choice([True, False]),
            'usingGoodsManagementModules': random.choice([True, False]),
        }

    def test_passValidData_withNoSeller__returnCreateSuccess(self):
        """

        :return:
        """
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        result = body['result']
        self.assertEqual(self.data['id'], result['id'])
        self.assertEqual(body['message'], 'Tạo mới seller thành công')

        seller = Seller.query.filter(
            Seller.id == result['id']
        ).first()

        self.assertEqual(self.data['name'], seller.name)
        self.assertEqual(self.data['code'], seller.code)
        self.assertEqual(self.data['isActive'], seller.status)
        self.assertEqual(self.data['isAutoGeneratedSku'], not seller.manual_sku)
        self.assertEqual(self.data['usingGoodsManagementModules'], not seller.is_manage_price)

    def test_passEmptyData__returnInvalidResponse(self):
        """

        :return:
        """
        code, body = self.call_api(data={
            "name": "",
            "code": "",
        })
        self.assertEqual(400, code)

    def test_missingName__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('name')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_missingCode__returnInvalidResponse(self):
        """

        :return:
        """
        self.data.pop('code')
        code, _ = self.call_api(data=self.data)

        self.assertEqual(400, code)

    def test_passValidData_withNoSeller__missingBooleanField__returnCreateSuccess(self):
        """

        :return:
        """
        self.data.pop('isActive')
        self.data.pop('isAutoGeneratedSku')
        self.data.pop('usingGoodsManagementModules')
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        result = body['result']
        self.assertEqual(self.data['id'], result['id'])
        self.assertEqual(body['message'], 'Tạo mới seller thành công')

        seller = Seller.query.filter(
            Seller.id == result['id']
        ).first()

        self.assertEqual(self.data['name'], seller.name)
        self.assertEqual(self.data['code'], seller.code)
        self.assertFalse(seller.status)
        self.assertTrue(seller.manual_sku)
        self.assertTrue(seller.is_manage_price)

    def tearDown(self):
        pass


class TestUpdateSeller(APITestCase):

    def url(self):
        return '/master-data/sellers'

    def method(self):
        return 'POST'

    def setUp(self):
        self.seller = fake.seller()
        self.data = {
            'id': self.seller.id,
            'name': fake.name(),
            'code': self.seller.code,
            'isActive': False,
            'isAutoGeneratedSku': True,
            'usingGoodsManagementModules': False,
        }

    def test_passValidData_withExistedSeller__returnUpdateSuccess(self):
        """

        :return:
        """
        code, body = self.call_api(data=self.data)

        self.assertEqual(200, code)
        result = body['result']
        self.assertEqual(self.data['id'], result['id'])

        seller = Seller.query.filter(
            Seller.id == result['id']
        ).first()

        self.assertEqual(self.data['name'], seller.name)
        self.assertEqual(self.data['code'], seller.code)
        self.assertFalse(seller.status)
        self.assertFalse(seller.manual_sku)
        self.assertTrue(seller.is_manage_price)

    def tearDown(self):
        pass
