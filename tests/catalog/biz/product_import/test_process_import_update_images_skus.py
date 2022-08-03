# coding=utf-8
import os
from abc import ABCMeta
from unittest.mock import patch

import config
from catalog import models
from catalog.biz.product_import.import_update_images_skus import ImportUpdateImagesSkus
from catalog.models import FileImport
from tests import logged_in_user
from tests.catalog.api import APITestCaseWithMysql
from tests.faker import fake


class MockResponse:
    def __init__(self, status_code, headers=None, content=None, image_url=None, url=None):
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.image_url = image_url
        self.url = url

    def json(self):
        return {
            'image_url': self.image_url,
            'url': self.url
        }


class ProcessImportUpdateImagesSkusTestCase(APITestCaseWithMysql, metaclass=ABCMeta):
    ISSUE_KEY = 'CATALOGUE-658'
    FOLDER = '/Import/process_update_images_skus'

    def setUp(self):

        self.patcher_1 = patch(
            'catalog.biz.product_import.import_update_images_skus.download_from_internet_and_upload_to_the_cloud',
            return_value='image_url_test')
        self.patcher_2 = patch('catalog.biz.product_import.import_update_images_skus.requests.post',
                               return_value=MockResponse(
                                   status_code=200,
                                   url='url_xlsx_test',
                               ))

        self.patcher_1.start()
        self.patcher_2.start()

        self.user = fake.iam_user(seller_id=fake.seller(manual_sku=False).id)

        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="123456789", seller_id=self.user.seller_id - 1,
                                                       variant_id=self.variant0.id)

        self.variant1 = fake.product_variant()
        self.sellable_product1 = fake.sellable_product(seller_sku="sku1", seller_id=self.user.seller_id, uom_ratio=1,
                                                       variant_id=self.variant1.id)
        self.image_sku1 = [fake.variant_product_image(product_variant_id=self.variant1.id) for _ in range(3)]

        self.variant2 = fake.product_variant()
        self.sellable_product2 = fake.sellable_product(seller_sku="sku2", seller_id=self.user.seller_id,
                                                       variant_id=self.variant2.id)
        self.image_sku2 = [fake.variant_product_image(product_variant_id=self.variant2.id) for _ in range(4)]

        self.variant3 = fake.product_variant()
        self.sellable_product3 = fake.sellable_product(seller_sku="sku3", seller_id=self.user.seller_id,
                                                       variant_id=self.variant3.id)
        self.image_sku3 = [fake.variant_product_image(product_variant_id=self.variant3.id) for _ in range(27)]

        self.variant4 = fake.product_variant()
        self.sellable_product4 = fake.sellable_product(seller_sku="sku4", seller_id=self.user.seller_id, uom_ratio=2,
                                                       variant_id=self.variant4.id)

        self.variant5 = fake.product_variant()
        self.sellable_product5 = fake.sellable_product(seller_sku="sku4", seller_id=self.user.seller_id, uom_ratio=1,
                                                       variant_id=self.variant5.id)

    def tearDown(self):
        self.patcher_1.stop()
        self.patcher_2.stop()

    def assert_first_row(self, file_name, message):
        file_stream = os.path.join(
            config.ROOT_DIR,
            'tests',
            'catalog',
            'api',
            'imports',
            'test_case_samples',
            'images_skus',
            file_name
        )

        process = FileImport()
        p = ImportUpdateImagesSkus(seller_id=self.user.seller_id,
                                   user_email=self.user.email,
                                   process=process,
                                   f_stream=file_stream)
        results = p.process()
        models.db.session().commit()
        self.assertTrue(1 == len(results), 'Enough row')
        self.assertEqual(message, results[0], f'Expected error: {message}')

    def test_process_not_found_sku(self):
        self.assert_first_row('not_found_sku_data.xlsx',
                              'Không tìm thấy sản phẩm (kiểm tra lại mã seller sku, '
                              'đơn vị tính và tỷ lệ quy đổi)')

    def test_process_more_than_one_sku(self):
        self.assert_first_row('multi_sku_data.xlsx', 'Tìm thấy nhiều hơn 1 sản phẩm có cùng mã seller sku. '
                                                     'Vui lòng nhập thêm đơn vị tính và tỷ lệ quy đổi')

    def test_process_not_manage_sku(self):
        self.assert_first_row('not_manage_sku.xlsx',
                              'Không tìm thấy sản phẩm (kiểm tra lại mã seller sku, '
                              'đơn vị tính và tỷ lệ quy đổi)')

    def test_process_over_36_image(self):
        self.assert_first_row('over_36_image.xlsx',
                              'Biến thể của ảnh không được vượt quá 36')

    def test_process_valid_seller_sku(self):
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku10", seller_id=self.user.seller_id,
                                                       is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.assert_first_row('valid_data_seller_sku.xlsx', '')

    def __get_uom_attr(self):
        uom_attr = models.Attribute.query.filter(models.Attribute.code == 'uom').first()
        if not uom_attr:
            uom_attr = fake.attribute(code='uom', value_type='selection', is_variation=True)
        return uom_attr

    def test_process_valid_seller_sku_and_uom(self):
        uom_attr = self.__get_uom_attr()
        uom_attr_option = fake.attribute_option(attribute_id=uom_attr.id, value='Bộ', seller_id=self.user.seller_id)
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku10", seller_id=self.user.seller_id,
                                                       uom_code=uom_attr_option.code, is_bundle=0,
                                                       variant_id=self.variant0.id)

        self.assert_first_row('valid_data_seller_sku_and_uom.xlsx', '')

    def test_process_valid_seller_sku_and_uom_and_ratio(self):
        uom_attr = self.__get_uom_attr()
        uom_attr_option = fake.attribute_option(attribute_id=uom_attr.id, value='Bộ', seller_id=self.user.seller_id)
        self.variant0 = fake.product_variant()
        self.sellable_product0 = fake.sellable_product(seller_sku="sku10", seller_id=self.user.seller_id,
                                                       uom_code=uom_attr_option.code, is_bundle=0, uom_ratio=1,
                                                       variant_id=self.variant0.id)

        self.assert_first_row('valid_data_seller_sku_and_uom_and_ratio.xlsx', '')

    def test_process_valid_data_match_image(self):
        file_stream = os.path.join(
            config.ROOT_DIR,
            'tests',
            'catalog',
            'api',
            'imports',
            'test_case_samples',
            'images_skus',
            'has_data.xlsx'
        )

        process = FileImport()
        p = ImportUpdateImagesSkus(seller_id=self.user.seller_id,
                                   user_email=self.user.email,
                                   process=process,
                                   f_stream=file_stream)
        results = p.process()
        models.db.session().commit()

        self.assertEqual(8, len(results), 'Enough row')
        self.assertEqual("", results[0], 'Success on sku with match case sensitive')
        self.assertEqual("", results[1], 'Success on sku with match case insensitive')
        self.assertEqual("", results[2], 'Ignore empty row')
        self.assertEqual('Không tìm thấy sản phẩm (kiểm tra lại mã seller sku, '
                         'đơn vị tính và tỷ lệ quy đổi)', results[3], 'sku not exists in db')
        self.assertEqual('Không tìm thấy sản phẩm (kiểm tra lại mã seller sku, '
                         'đơn vị tính và tỷ lệ quy đổi)', results[4],
                         'sku exists in db but do not belong to seller')
        self.assertTrue("" == results[5], 'Ignore empty images')
        self.assertTrue("" == results[6], 'Ignore empty sku')
        self.assertTrue("Biến thể của ảnh không được vượt quá 36" == results[7], 'Over 36 image')

        image_db1 = models.VariantImage.query.filter(models.VariantImage.product_variant_id == self.variant1.id) \
            .order_by(models.VariantImage.priority).all()
        self.assertTrue(len(self.image_sku1) + 2 == len(image_db1), 'matching insert images')

        for i in range(2):
            self.assertTrue(image_db1[i].url == 'image_url_test', 'image at top')

        image_db2 = models.VariantImage.query.filter(models.VariantImage.product_variant_id == self.variant2.id) \
            .order_by(models.VariantImage.priority).all()
        self.assertTrue(len(self.image_sku2) + 4 == len(image_db2), 'matching insert images')
        for i in range(4):
            self.assertTrue(image_db2[i + len(self.image_sku2)].url == 'image_url_test', 'image at last')

        self.assertEqual(process.total_row_success, 2, 'total row success do not match')

        self.assertEqual(process.status, 'done')
        self.assertEqual(p.skus, [self.sellable_product1.sku, self.sellable_product2.sku])
