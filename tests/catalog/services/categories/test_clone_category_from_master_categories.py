# coding=utf-8

import json
import logging
from mock import patch

import config
from catalog.services.categories import CategoryService
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake

__author__ = 'quang.da'
__logger__ = logging.getLogger(__name__)

service = CategoryService.get_instance()


class CatalogServiceCloneFromMasterCategoryTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-296'
    FOLDER = '/Category/Clone'

    def setUp(self):
        self.seller = fake.seller()
        self.master_cat = fake.master_category(is_active=True)
        self.child_master_cat = fake.master_category(parent_id=self.master_cat.id, is_active=True)

    @patch('catalog.biz.category.publish_category')
    def test_cloneCategory_successfully(self, mock):
        mock.return_value = None
        service.clone_top_level_cat(self.master_cat.id, self.seller.id)
        list_cat, count = service.get_list_categories({})
        assert count == 2

    @patch('catalog.biz.category.publish_category')
    def test_cloneCategoryWithOneChild_successfully(self, mock):
        mock.return_value = None
        service.clone_top_level_cat(self.master_cat.id, self.seller.id)
        list_cat, count = service.get_list_categories({})
        assert count == 2

    def test_cloneCategoryNotExisted_returnNone(self):
        fake_master_cat_id = self.master_cat.id + self.child_master_cat.id
        clone_master_cat = service.clone_top_level_cat(fake_master_cat_id, self.seller.id)
        assert clone_master_cat == False

    @patch('catalog.biz.category.publish_category')
    def test_cloneCategoryWithManyChildren_successfully(self, mock):
        mock.return_value = None
        fake.master_category(parent_id=self.master_cat.id, is_active=True)
        fake.master_category(parent_id=self.master_cat.id, is_active=True)
        service.clone_top_level_cat(self.master_cat.id, self.seller.id)
        list_cat, count = service.get_list_categories({}, )
        assert count == 4

    def test_cloneCategoryAlreadyClonedBefore_returnNone(self):
        fake.category(master_category_id=self.master_cat.id, seller_id=self.seller.id)
        clone_master_cat = service.clone_top_level_cat(self.master_cat.id, self.seller.id)
        assert clone_master_cat == False
