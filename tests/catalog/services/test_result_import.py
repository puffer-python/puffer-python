from unittest import TestCase
from mock import patch
from tests.utils import JiraTest
from werkzeug.test import EnvironBuilder
from pandas import Series
from catalog import app
from catalog.biz.result_import import (
    CreateProductImportCapture,
    CreateProductImportSaver,
    ImportStatus,
)

class CaptureTestCase(TestCase, JiraTest):
    def innerFunction(self):
        pass

    def runCapture(self, importer, parent_row=None, inner_fn=None):
        environ = EnvironBuilder().get_environ()
        with app.request_context(environ):
            with CreateProductImportCapture(1, parent_row, 1, importer) as capture:
                if inner_fn:
                    inner_fn()

        return capture

class FakeImporter():
    row = None

class CreateProductCaptureTestCase(CaptureTestCase):
    ISSUE_KEY = 'CATALOGUE-365'

    def test_passDONRowOfDataFrame__callCeleryJobOnce(self):
        fake_importer = FakeImporter()
        fake_importer.row = Series({
            'field 1': 'value 1',
            'field 2': 2,
            'field 3': {
                'field 4': None,
                'field 5': True
            }
        })
        with patch('catalog.biz.result_import.capture_import_result.delay') as mock_call_job:
            mock_call_job.return_value = None
            capture = self.runCapture(fake_importer)

            mock_call_job.assert_called_once()
            assert capture.attribute_set_id == 1
            assert capture.data == fake_importer.row.to_dict()
            assert capture.import_id == 1
            assert len(capture.tag) == 32

    def test_passDONRowOfDataFrameWithError__StatusIsFatal(self):
        fake_importer = FakeImporter()
        fake_importer.row = Series({
            'field 1': 'value 1',
            'field 2': 2,
            'field 3': {
                'field 4': None,
                'field 5': True
            }
        })

        def error_fn():
            raise Exception('unexpected error')

        with patch('catalog.biz.result_import.capture_import_result.delay') as mock_call_job:
            mock_call_job.return_value = None
            capture = self.runCapture(fake_importer, inner_fn=error_fn)

            assert capture.attribute_set_id == 1
            assert capture.data == fake_importer.row.to_dict()
            assert capture.import_id == 1
            assert len(capture.tag) == 32
            assert capture.status == ImportStatus.FATAL
