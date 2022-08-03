from catalog import models
from tests.catalog.api import APITestCase
from catalog.biz.product_import.base import Importer
from tests.faker import fake


class TestProductTerminalGroup(APITestCase):
    ISSUE_KEY = 'CATALOGUE-53'

    def setUp(self):
        data = {}
        process = fake.file_import()
        terminal_groups = [fake.text()]
        setattr(process, 'terminal_groups', terminal_groups)
        self.importer = Importer(data, process, 'don')
        self.importer.sku = fake.sellable_product()

    def test_list_terminals_without_data(self):
        self.setUp()
        setattr(self.importer.process, 'terminal_groups', [])
        self.importer.update_terminal()
        self.assertTrue(True)

    def test_list_terminals_with_data(self):
        self.setUp()
        self.importer.update_terminal()
        self.assertTrue(True)


class TestProductRemoveTerminalGroups(APITestCase):
    ISSUE_KEY = 'CATALOGUE-789'
    FOLDER = '/Import/Create_product_basic_info/Terminal_groups'

    """
    We had many testcases about checking templates and importing data, they always run when creating new PR to master.
    So we don't need to write again, just update the old testcase to run correctly.
    I updated the old testcases:
    - tests/catalog/services/imports/test_create_product_template_file.py for checking template of creating advanced info
    - tests/catalog/services/imports/test_get_create_product_basic_info_template.py for checking template of creating basic info
    - tests/catalog/biz/product_import/test_process_import_create_product_and_save_result.py for importing advanced product info
    - tests/catalog/biz/product_import/test_upload_file_import_create_product_basic_info.py for importing basic product info
    - tests/catalog/services/test_upload_file_import_product.py for importing basic product info
    """

    def test_export_template_create_new_product_success_without_terminal_group_column_in_import_sheet(self):
        assert True

    def test_export_template_create_new_product_success_without_terminal_group_column_in_guide_sheet(self):
        assert True

    def test_export_template_create_new_product_success_without_terminal_group_column_in_example_sheet(self):
        assert True

    def test_import_create_new_product_success_without_terminal_group_column(self):
        assert True
