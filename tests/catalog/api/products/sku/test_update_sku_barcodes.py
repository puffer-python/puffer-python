# coding=utf-8
# pylint: disable=E0401
from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake


class TestUpdateSKuBarcodes(APITestCase):
    ISSUE_KEY = 'CATALOGUE-853'
    FOLDER = '/Sku/UpdateSku/Barcodes'

    def __get_url(self, sku=None):
        return f'/skus/{sku or self.sku.sku}'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.product = fake.product(category_id=self.category.id,
                                    master_category_id=self.master_category.id,
                                    created_by='quanglm')
        self.variant = fake.product_variant(product_id=self.product.id, uom_ratio_value=1)
        self.sku = fake.sellable_product(variant_id=self.variant.id, barcode=fake.text(20),
                                         seller_id=self.category.seller_id)

    def __init_payload(self, barcode=None, same_barcode=True, add_new_seller=False):
        seller_id = self.category.seller_id
        if add_new_seller:
            seller_id = fake.seller().id
        variant = fake.product_variant(product_id=self.product.id, uom_ratio_value=1)
        self.sku = fake.sellable_product(variant_id=variant.id, seller_id=seller_id, barcode=fake.text(10))
        barcode = barcode or fake.text(30)
        new_barcode = barcode if same_barcode else fake.text(30)
        barcodes_with_source = [{'barcode': new_barcode, 'source': fake.text(100)},
                                {'barcode': fake.text(30), 'source': fake.text(100)}]
        self.payload = {
            'barcodes': barcodes_with_source
        }

    def _equal(self, barcodes_with_source):
        barcodes = list(map(lambda x: x.get('barcode'), barcodes_with_source))
        sku_barcodes = models.SellableProductBarcode.query \
            .filter(models.SellableProductBarcode.sellable_product_id == self.sku.id).all()
        self.assertEqual(barcodes[-1], self.sku.barcode)
        for sb in sku_barcodes:
            self.assertEqual(sb.id == sku_barcodes[-1].id, sb.is_default)
        for barcode_with_source in barcodes_with_source:
            sb = next(filter(lambda x: x.barcode == barcode_with_source.get('barcode'), sku_barcodes))
            self.assertEqual(barcode_with_source.get('barcode'), sb.barcode)
            self.assertEqual(barcode_with_source.get('source'), sb.source)

    def test_return200__with_same_barcode_in_different_sellers(self):
        barcode = fake.text(25)
        self.__init_payload(barcode=barcode)
        new_seller_id = fake.seller().id
        new_sku = fake.sellable_product(variant_id=self.sku.variant_id, seller_id=new_seller_id, barcode=barcode)

        fake.sellable_product_barcode(sku_id=new_sku.id, barcode=barcode)
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(200, code)
        self._equal(self.payload.get('barcodes'))

    def test_return200__with_different_barcodes_same_seller(self):
        self.__init_payload()
        new_sku = fake.sellable_product(
            variant_id=self.sku.variant_id, seller_id=self.sku.seller_id,
            barcode=fake.text(25)
        )

        fake.sellable_product_barcode(sku_id=new_sku.id, barcode=new_sku.barcode)
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(200, code, body)
        self._equal(self.payload.get('barcodes'))

    def test_return200__with_different_barcodes_different_sellers(self):
        barcode = fake.text(25)
        self.__init_payload()
        new_seller_id = fake.seller().id
        new_sku = fake.sellable_product(variant_id=self.sku.variant_id, seller_id=new_seller_id, barcode=barcode)

        fake.sellable_product_barcode(sku_id=new_sku.id, barcode=barcode)
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(200, code)
        self._equal(self.payload.get('barcodes'))

    def test_return400__barcode__exceed_30(self):
        self.__init_payload(barcode=fake.text(31))
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual('Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', body['message'])

    def test_return400__source_exceed_255(self):
        self.__init_payload()
        self.payload['barcodes'][0]['source'] = fake.text(256)
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual('Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', body['message'])

    def test_return400__empty_list_barcodes(self):
        self.__init_payload()
        self.payload['barcodes'] = []
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual('Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', body['message'])

    def test_return400__empty_barcode_in_list_barcodes(self):
        self.__init_payload()
        self.payload['barcodes'][0]['barcode'] = ''
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual('Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', body['message'])

    def test_return400__empty_source_in_list_barcodes(self):
        self.__init_payload()
        self.payload['barcodes'][0]['source'] = '   '
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual('Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', body['message'])

    def test_return400__duplicated_barcode_in_payload(self):
        self.__init_payload()
        self.payload['barcodes'][0]['barcode'] = self.payload['barcodes'][1]['barcode']
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual(f"barcode {self.payload['barcodes'][0]['barcode']} bị trùng lặp", body['message'])

    def test_return400__duplicated_barcode_in_same_seller(self):
        barcode = fake.text(25)
        self.__init_payload(barcode=barcode)
        new_sku = fake.sellable_product(variant_id=self.sku.variant_id, seller_id=self.sku.seller_id, barcode=barcode)
        fake.sellable_product_barcode(sku_id=new_sku.id, barcode=new_sku.barcode)
        code, body = self.call_api(self.payload, url=self.__get_url())
        self.assertEqual(400, code)
        self.assertEqual(f"barcode {self.payload['barcodes'][0]['barcode']} của SKU {new_sku.seller_sku} đã tồn tại",
                         body['message'])

    def test_return400__not_found_sku(self):
        self.__init_payload()
        code, body = self.call_api(self.payload, url=self.__get_url(sku=f'1{self.sku.sku}1'))
        self.assertEqual(400, code)
        self.assertEqual('Không tồn tại sản phẩm', body['message'])
