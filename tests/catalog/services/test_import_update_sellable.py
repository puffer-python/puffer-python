from unittest import TestCase

import pytest
import requests
from unittest.mock import patch
import pandas as pd
from tests.utils import JiraTest
from tests import logged_in_user
from tests.faker import fake
from catalog import app
from catalog.biz.product_import import import_update


class ImportUpdateTestCase(TestCase, JiraTest):
    ISSUE_KEY = 'CATALOGUE-214'

    def setUp(self):
        self.seller = fake.seller()
        self.sellables = [fake.sellable_product(seller_id=self.seller.id) for _ in range(10)]
        self.data = {
            'sku': [x.sku for x in self.sellables],
            'product name': [fake.name() for _ in self.sellables],
        }

    @patch('catalog.biz.product_import.import_update.GeneralUpdateImporter._fetch_file_import', return_value=None)
    @patch('catalog.biz.product_import.import_update.GeneralUpdateImporter.upload_result_to_server', return_value='')
    def run_executor(self, *args):
        task = fake.file_import(status='new')
        executor = import_update.GeneralUpdateImporter(task.id)
        executor.df = pd.DataFrame.from_dict(self.data)
        executor.task = task
        executor.excel_field_names = executor.df.columns
        with logged_in_user(fake.iam_user(seller_id=self.seller.id)):
            executor.run()
        return executor

    @pytest.mark.skip(reason='Update version for LIB, fix it late')
    def test_success(self):
        executor = self.run_executor()
        assert executor.task.status == 'done'

        for sellable in self.sellables:
            idx = self.data['sku'].index(sellable.sku)
            assert self.data['product name'][idx] == sellable.name, executor.result.iloc[idx]['Message']
