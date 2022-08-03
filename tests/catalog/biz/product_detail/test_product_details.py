# # coding=utf-8
# import json
# import time
# import pytest
# from sqlalchemy import text
# from tests.faker import fake
# from tests.catalog.api import APITestCaseWithMysql
# from catalog.utils.sql_functions import select_and_insert_json
# from catalog import models as m
#
#
# @pytest.mark.usefixtures('functions_product_details')
# class TestProductDetailTerminalGroups(APITestCaseWithMysql):
#     ISSUE_KEY = 'CATALOGUE-790'
#     FOLDER = '/ProductDetails/TerminalGroups'
#
#     def setUp(self):
#         self.sku = fake.sellable_product(sku=f'{fake.integer()}{round(time.time() * 1000)}')
#         m.db.session.commit()
#
#     def __get_product_detail(self):
#         params = {'sku': self.sku.sku}
#         results = m.db.engine.execute(text('select `data` from product_details where sku = :sku'), params)
#         for r in results:
#             return json.loads(r.data)
#
#     def test_sync_product_details_no_terminals(self):
#         select_and_insert_json(self.sku.sku, updated_by='quanglm')
#         data = self.__get_product_detail()
#         self.assertEqual(self.sku.sku, data['sku'])
#         self.assertTrue('seller_categories' in data)
#         self.assertTrue('terminals' in data)
#
#     def test_sync_product_details_no_terminal_groups(self):
#         select_and_insert_json(self.sku.sku, updated_by='quanglm')
#         data = self.__get_product_detail()
#         self.assertEqual(self.sku.sku, data['sku'])
#         self.assertTrue('seller_categories' in data)
#         self.assertTrue('terminal_groups' in data)
