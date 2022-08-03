#coding=utf-8

from unittest import TestCase

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.master_categories.master_category import MasterCategoryService
from tests.utils import JiraTest


service = MasterCategoryService.get_instance()


class CreateMasterCategoryTestCase(APITestCase, JiraTest):
    ISSUE_KEY = 'SC-659'

    def test_saveMasterCategory(self):
        grandfather = fake.master_category(is_active=True)
        father = fake.master_category(parent_id=grandfather.id, is_active=True)
        data = {
            'name': fake.name(),
            'code': fake.hexify('????'),
            'parent_id': father.id
        }
        category = service.create_master_category(data)
        assert category.depth == 3
        assert category.path == f'{grandfather.id}/{father.id}/{category.id}'
