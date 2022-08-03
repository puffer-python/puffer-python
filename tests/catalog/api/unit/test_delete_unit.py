# coding=utf-8
import logging

from mock import patch

from catalog.models import Unit
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'Minh.ND'
_logger = logging.getLogger(__name__)


class TestDeleteUnit(APITestCase):
    ISSUE_KEY = 'SC-607'

    def url(self):
        return '/units/{unit_id}'

    def method(self):
        return 'DELETE'

    def setUp(self):
        self.patcher = patch('catalog.extensions.signals.unit_deleted_signal.send')
        self.mock_signal = self.patcher.start()
        self.unit = fake.unit()

    def test__returnDeleteSuccess(self):
        unit_id = self.unit.id

        code, body = self.call_api(url=self.url().format(unit_id=self.unit.id))
        self.assertEqual(200, code)

        unit = Unit.query.filter(Unit.id == unit_id).all()

        self.assertEqual(len(unit), 0)
        self.mock_signal.assert_called_once()

    def test_deleteAUnitInSellableProduct__returnBadRequest(self):
        fake.sellable_product(unit_id=self.unit.id)

        code, body = self.call_api(url=self.url().format(unit_id=self.unit.id))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Không thể xóa, đơn vị tính đang được sử dụng')

        self.mock_signal.assert_not_called()

    def test_deleteAUnitPoInSellableProduct__returnBadRequest(self):
        fake.sellable_product(unit_po_id=self.unit.id)

        code, body = self.call_api(url=self.url().format(unit_id=self.unit.id))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Không thể xóa, đơn vị tính đang được sử dụng')

        self.mock_signal.assert_not_called()

    def test_deleteAUnitInProduct__returnBadRequest(self):
        fake.product(unit_id=self.unit.id)

        code, body = self.call_api(url=self.url().format(unit_id=self.unit.id))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Không thể xóa, đơn vị tính đang được sử dụng')

    def test_deleteAUnitPoInProduct__returnBadRequest(self):
        fake.product(unit_po_id=self.unit.id)

        code, body = self.call_api(url=self.url().format(unit_id=self.unit.id))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Không thể xóa, đơn vị tính đang được sử dụng')

        self.mock_signal.assert_not_called()

    def test_passNonExistenceUnitId__returnBadRequest(self):
        code, body = self.call_api(url=self.url().format(unit_id=123))

        self.assertEqual(code, 400)
        self.assertEqual(body['message'], 'Tên đơn vị tính không tồn tại')

    def test_passInValidUnitId__returnNotFound(self):
        code, body = self.call_api(url=self.url().format(unit_id='abc'))

        self.assertEqual(code, 404)

    def tearDown(self):
        self.patcher.stop()
