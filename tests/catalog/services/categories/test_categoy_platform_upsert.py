# coding=utf-8
import logging

__author__ = 'Dung.BV'
__logger__ = logging.getLogger(__name__)

from abc import ABC

from unittest.mock import patch

from catalog.extensions.ram_queue_consumer import _process_category_upsert
from catalog.models import db
from tests.catalog.api import APITestCase
from tests.faker import fake


class TestCategoryPlatformUpsert(APITestCase, ABC):

    @patch('catalog.extensions.queue_publisher.QueuePublisher.publish_message')
    @patch('catalog.services.seller.get_seller_by_id')
    def testCreateCategoryPlatform(self, get_seller_mocker, mock_push_message):
        get_seller_mocker.return_value = {
            'servicePackage': fake.text(),
        }
        mock_push_message.return_value = True

        self.category = fake.category()
        fake.platform_sellers(
            seller_id=self.category.seller_id, platform_id=self.category.seller_id,
            is_default=True, is_owner=True
        )
        messages = _process_category_upsert(db.session, {'id': self.category.id})
        self.assertIsNotNone(messages)
        self.assertGreater(len(messages), 0)
        for message in messages:
            self.assertEqual(message.sellerId, self.category.seller_id)

    @patch('catalog.extensions.queue_publisher.QueuePublisher.publish_message')
    @patch('catalog.services.seller.get_seller_by_id')
    def testUpdateCategoryPlatform(self, get_seller_mocker, mock_push_message):
        get_seller_mocker.return_value = {
            'servicePackage': fake.text(),
        }
        mock_push_message.return_value = True
        self.category = fake.category()
        fake.platform_sellers(
            seller_id=self.category.seller_id, platform_id=self.category.seller_id,
            is_default=True, is_owner=True
        )
        messages = _process_category_upsert(db.session, {'id': self.category.id}, 'updated')
        self.assertIsNotNone(messages)
        self.assertGreater(len(messages), 0)
        for message in messages:
            self.assertEqual(message.sellerId, self.category.seller_id)
