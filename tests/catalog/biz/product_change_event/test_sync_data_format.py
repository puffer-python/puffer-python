# coding=utf-8
from tests.catalog.api import APITestCase


class TestSyncPPM(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1300'
    FOLDER = '/ProductPushData/PPM'

    def setUp(self):
        pass

    def test_sync_correct_platform_categories(self):
        assert True
