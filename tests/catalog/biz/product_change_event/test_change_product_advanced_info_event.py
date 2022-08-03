# coding=utf-8
import logging

from tests.catalog.api import APITestCase

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class SellableProductChangeAdvancedInfoTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-687'
    FOLDER = '/Product/AdvancedInfo/Event'

    def test_update_success__with_new_sku(self):
        assert True

    def test_update_success__with_change_sku_name(self):
        assert True

    def test_update_success__with_change_sku_short_description(self):
        assert True

    def test_update_success__with_change_sku_description(self):
        assert True

    def test_update_success__with_change_seo_name(self):
        assert True

    def test_update_success__with_change_seo_short_description(self):
        assert True

    def test_update_success__with_change_seo_smart_showroom(self):
        assert True

    def test_update_success__with_change_seo_meta_title(self):
        assert True

    def test_update_success__with_change_seo_meta_keyword(self):
        assert True

    def test_update_success__with_change_seo_meta_description(self):
        assert True

    def test_update_success__with_change_attribute_name(self):
        assert True

    def test_update_success__with_change_attribute_display_name(self):
        assert True

    def test_update_success__with_change_attribute_config_priority(self):
        assert True

    def test_update_success__with_change_attribute_config_searchable(self):
        assert True

    def test_update_success__with_change_attribute_config_filterable(self):
        assert True

    def test_update_success__with_change_attribute_config_comparable(self):
        assert True

    def test_update_success__with_change_unit_name(self):
        assert True

    def test_update_success__with_change_attribute_option_value(self):
        assert True

    def test_update_success__with_change_attribute_group_config_text_before(self):
        assert True

    def test_update_success__with_change_attribute_group_config_text_after(self):
        assert True

    def test_update_success__with_change_attribute_group_config_display(self):
        assert True

    def test_update_success__with_change_attribute_group_config_highlight(self):
        assert True

    def test_update_success__with_change_attribute_group_config_flat(self):
        assert True

    def test_update_success__with_change_attribute_group_config_priority(self):
        assert True

    def test_update_success__with_add_new_attribute_group(self):
        assert True

    def test_update_success__with_add_remove_attribute_group(self):
        assert True

    def test_update_failed__with_exception(self):
        assert True
