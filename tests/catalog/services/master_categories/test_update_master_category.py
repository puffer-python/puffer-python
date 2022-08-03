#coding=utf-8

from unittest import TestCase

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.master_categories.master_category import MasterCategoryService
from tests.utils import JiraTest


service = MasterCategoryService.get_instance()


class UpdateMasterCategoryTestCase(APITestCase, JiraTest):
    ISSUE_KEY = 'SC-660'

    def test_saveMasterCategory(self):
        father = fake.master_category(is_active=True)
        me = fake.master_category(parent_id=father.id, is_active=True)
        neighbor = fake.master_category(is_active=True)
        my_child = fake.master_category(parent_id=me.id, is_active=True)
        data = {
            'is_active': False,
            'parent_id': neighbor.id
        }
        me = service.update_master_category(me.id, data)
        assert me.is_active == False
        assert me.parent_id == neighbor.id
        assert my_child.is_active
        assert me.path.split('/')[0] == str(neighbor.id)
        assert my_child.path.split('/')[0] == str(neighbor.id)
        assert len(my_child.path.split('/')) == my_child.depth
