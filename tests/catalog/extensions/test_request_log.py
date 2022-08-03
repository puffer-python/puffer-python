import json
import time
from mock import patch

from catalog import log_request, models as m
from tests.catalog.api import APITestCase


@log_request
def do_something(sleep=0):
    if sleep > 0:
        time.sleep(sleep)
    return {'foo': 'bar'}


class TestRequetsLog(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1438'
    FOLDER = '/RequestLog'

    def test_save_request_log_successfully(self):
        res = do_something()
        request_log = m.RequestLog.query.first()

        self.assertEqual(json.dumps(res, ensure_ascii=False), request_log.response_body)

    def test_save_request_log_failed_but_not_affect_to_main_function(self):
        with patch('json.dumps', side_effect=Exception('mocked error')):
            res = do_something()
            request_log = m.RequestLog.query.first()

            self.assertIsNone(request_log)
            self.assertDictEqual({'foo': 'bar'}, res)

    def test_save_request_log_append_only(self):
        res = do_something(3)
        request_log = m.RequestLog.query.first()
        diff_seconds = (request_log.updated_at - request_log.created_at).seconds

        self.assertEqual(json.dumps(res, ensure_ascii=False), request_log.response_body)
        self.assertGreater(1, diff_seconds)
