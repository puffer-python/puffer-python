# coding=utf-8

import json
import logging

import pytest
import responses
from mock import patch

import config
from catalog.biz.category.category import create_categories_on_SRM
from catalog.services.categories import CategoryService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from unittest.mock import MagicMock

__author__ = 'chung.hd'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class CatalogServiceCloneFromMasterCategoryTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-387'
    FOLDER = '/Category/Clone'

    def setUp(self):
        self.seller = fake.seller()
        self.category = fake.category(is_active=True, seller_id=self.seller.id)

    @responses.activate
    def test_callApiToSrmReturn200_successSendCreateCategoryMessage(self):
        responses.add(responses.POST, config.SRM_SERVICE_URL + '/categories',
                      json={}, status=200)
        service = CategoryService.get_instance()
        service.create_category_on_srm = MagicMock()
        create_categories_on_SRM(category_ids=[self.category.id], seller_id=self.seller.id)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == config.SRM_SERVICE_URL + '/categories'
        service.create_category_on_srm.assert_called()


    @responses.activate
    def test_callApiToSrmNotReturn200_notSendCreateCategoryMessage(self):
        responses.add(responses.POST, config.SRM_SERVICE_URL + '/categories',
                      json={}, status=400)
        service = CategoryService.get_instance()
        service.create_category_on_srm = MagicMock()
        create_categories_on_SRM(category_ids=[self.category.id], seller_id=self.seller.id)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == config.SRM_SERVICE_URL + '/categories'
        service.create_category_on_srm.assert_not_called()

    @responses.activate
    def test_callApiToSrmNotReturn200_callDelay1Hour(self):
        responses.add(responses.POST, config.SRM_SERVICE_URL + '/categories',
                      json={}, status=400)
        service = CategoryService.get_instance()
        service.create_category_on_srm = MagicMock()
        create_categories_on_SRM.apply_async = MagicMock()
        create_categories_on_SRM(category_ids=[self.category.id], seller_id=self.seller.id)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == config.SRM_SERVICE_URL + '/categories'
        service.create_category_on_srm.assert_not_called()
        create_categories_on_SRM.apply_async.assert_called_once_with(
            countdown=config.SYNC_CATEGORY_TO_SRM_DELAY_TIME,
            kwargs={"category_ids": [self.category.id], "seller_id": self.seller.id, "retried_time": 1}
        )

    @responses.activate
    def test_callApiToSrmNotReturn200_recallApiSrmAfter1Hour(self):
        responses.add(responses.POST, config.SRM_SERVICE_URL + '/categories',
                      json={}, status=400)
        service = CategoryService.get_instance()
        service.create_category_on_srm = MagicMock()
        create_categories_on_SRM.apply_async = MagicMock()
        create_categories_on_SRM(category_ids=[self.category.id], seller_id=self.seller.id)

        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == config.SRM_SERVICE_URL + '/categories'
        service.create_category_on_srm.assert_not_called()
        create_categories_on_SRM.apply_async.assert_called_once_with(
            countdown=config.SYNC_CATEGORY_TO_SRM_DELAY_TIME,
            kwargs={"category_ids": [self.category.id], "seller_id": self.seller.id, "retried_time": 1}
        )
