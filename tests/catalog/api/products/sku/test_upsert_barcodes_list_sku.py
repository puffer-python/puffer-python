# coding=utf-8
# pylint: disable=E0401
from catalog import models
import random

from tests.catalog.api import APITestCase
from tests.faker import fake


class TestCreateListSKuLayerSKUBarcodes(APITestCase):
    ISSUE_KEY = 'CATALOGUE-854'
    FOLDER = '/Sku/CreateListSku/SkuLayer/Barcodes'

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

    def setUp(self):
        self.created_by = 'quanglm'
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.product = fake.product(category_id=self.category.id,
                                    master_category_id=self.master_category.id,
                                    created_by=self.created_by)

    def __init_payload(self, barcodes, number_skus=1, update_sku=False, **kwargs):
        variants = [fake.product_variant(product_id=self.product.id, uom_ratio_value=2) for _ in range(number_skus)]

        payload_variants = []
        for i, x in enumerate(variants):
            variant = {'variantId': x.id}

            if not update_sku:
                variant['sku'] = {
                    'images': [],
                    'trackingType': False,
                    'expiryTracking': False,
                    'expirationType': random.choice([1, 2]),
                    'daysBeforeExpLock': fake.integer(),
                    'productType': random.choice(['product', 'consu']),
                    'sellerSku': fake.text(),
                    'barcodes': barcodes[i]
                }
            else:
                sku = fake.sellable_product(variant_id=x.id, seller_id=self.category.seller_id, **kwargs)
                fake.sellable_product_barcode(sku_id=sku.id, barcode=fake.text(25), is_default=True)
                variant['sku'] = {
                    'sku': sku.sku,
                    'barcodes': barcodes[i]
                }
            payload_variants.append(variant)

        self.payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'productId': self.product.id,
            'providerId': 2,
            'variants': payload_variants
        }

    def __init_payload_with_new_sku_barcode(self, barcode=None, same_barcode=True, add_new_seller=False,
                                            update_sku=False, add_source=True):
        seller_id = self.category.seller_id
        if add_new_seller:
            seller_id = fake.seller().id
        variant = fake.product_variant(product_id=self.product.id, uom_ratio_value=1)
        self.sku = fake.sellable_product(variant_id=variant.id, seller_id=seller_id, barcode=fake.text(10))
        barcode = barcode or fake.text(30)
        new_barcode = barcode if same_barcode else fake.text(30)
        fake.sellable_product_barcode(sku_id=self.sku.id, barcode=barcode)
        if add_source:
            barcodes_with_source = [[{'barcode': new_barcode, 'source': fake.text(100)},
                                     {'barcode': fake.text(30), 'source': fake.text(100)}]]
        else:
            barcodes_with_source = [[new_barcode, fake.text(30)]]
        self.__init_payload(barcodes_with_source, update_sku=update_sku)
        return barcodes_with_source

    def _equal(self, new_sku, all_barcodes_with_source):
        barcodes = []
        for barcodes_with_source in all_barcodes_with_source:
            barcodes.extend(map(lambda x: x if isinstance(x, str) else x.get('barcode'), barcodes_with_source))
        sellable = models.SellableProduct.query.filter(models.SellableProduct.sku == new_sku).first()
        sku_barcodes = models.SellableProductBarcode.query \
            .filter(models.SellableProductBarcode.sellable_product_id == sellable.id).all()
        self.assertEqual(barcodes[-1], sellable.barcode)
        for sb in sku_barcodes:
            self.assertEqual(sb.id == sku_barcodes[-1].id, sb.is_default)
        for barcodes_with_source in all_barcodes_with_source:
            for barcode_with_source in barcodes_with_source:
                barcode, source = barcode_with_source, None
                if not isinstance(barcode_with_source, str):
                    barcode = barcode_with_source.get('barcode')
                    source = barcode_with_source.get('source')

                sb = next(filter(lambda x: x.barcode == barcode, sku_barcodes))
                self.assertEqual(barcode, sb.barcode)
                self.assertEqual(source, sb.source)

    def test_create_success_return200__with_only_barcodes_and_same_barcode_in_different_sellers(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=True, add_source=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_create_success_return200__with_same_barcode_in_different_sellers(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=True)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_update_success_return200__with_same_barcode_in_different_sellers(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=True, update_sku=True)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_create_success_return200__with_different_barcodes_same_seller(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, same_barcode=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_update_success_return200__with_different_barcodes_same_seller(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, same_barcode=False,
                                                                        update_sku=True)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_update_success_return200__with_keep_barcode_field(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, same_barcode=False,
                                                                        update_sku=True, add_source=False)
        self.payload['variants'][0]['sku']['barcode'] = self.payload['variants'][0]['sku'].pop('barcodes')
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        sellable = models.SellableProduct.query.filter(
            models.SellableProduct.sku == body['result']['variants'][0]['sku']).first()
        sku_barcodes = models.SellableProductBarcode.query \
            .filter(models.SellableProductBarcode.sellable_product_id == sellable.id).all()
        self.assertEqual(barcodes_with_source[0][-1], sellable.barcode)
        self.assertEqual(len(sku_barcodes), len(barcodes_with_source[0]))

    def test_create_success_return200__with_different_barcodes_different_sellers(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=True, same_barcode=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_update_success_return200__with_different_barcodes_different_sellers(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=True, same_barcode=False,
                                                                        update_sku=True)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)

    def test_update_success_return200__without_change_old_barcodes(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, same_barcode=False,
                                                                        update_sku=True)
        old_barcodes = models.SellableProductBarcode.query.filter(
            models.SellableProductBarcode.sellable_product_id == self.sku.id).all()
        code, body = self.call_api(self.payload)
        all_barcodes = models.SellableProductBarcode.query.filter(
            models.SellableProductBarcode.sellable_product_id == self.sku.id).all()
        self.assertEqual(200, code)
        self._equal(body['result']['variants'][0]['sku'], barcodes_with_source)
        for old_barcode in old_barcodes:
            cur_barcode = next(filter(lambda x: x.id == old_barcode.id, all_barcodes))
            self.assertEqual(old_barcode.barcode, cur_barcode.barcode)
            self.assertEqual(old_barcode.source, cur_barcode.source)
            self.assertEqual(old_barcode.created_by, cur_barcode.created_by)
            self.assertEqual(old_barcode.created_at, cur_barcode.created_at)
            self.assertEqual(old_barcode.updated_at, cur_barcode.updated_at)

    def test_return400__barcode__not_list(self):
        self.__init_payload([{'barcode': fake.text(10)}])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', body['message'])

    def test_return400__barcode__more_fields(self):
        self.__init_payload([[{'barcode': fake.text(31), 'xxx': 'abc'}]])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('barcodes không hợp lệ', body['message'])

    def test_return400__barcode__exceed_30(self):
        self.__init_payload([[{'barcode': fake.text(31)}]])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('barcodes không hợp lệ', body['message'])

    def test_return400__source_exceed_255(self):
        self.__init_payload([[{'barcode': fake.text(30), 'source': fake.text(256)}]])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('barcodes không hợp lệ', body['message'])

    def test_return400__empty_barcode_in_list_barcodes(self):
        self.__init_payload([[{'barcode': None, 'source': fake.text(255)}]])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual('barcodes không hợp lệ', body['message'])

    def test_return400__duplicated_barcode_in_payload_of_a_sku(self):
        same_barcode = fake.text(30)
        self.__init_payload([[{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': same_barcode, 'source': fake.text(255)}]])
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(f'barcode {same_barcode} bị trùng lặp', body['message'])

    def test_return400__duplicated_barcode_in_payload_of_multiple_skus_only_create(self):
        same_barcode = fake.text(30)
        self.__init_payload([[{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': fake.text(30), 'source': fake.text(255)}],
                             [{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': fake.text(30), 'source': fake.text(255)}]
                             ], number_skus=2)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(f'barcode {same_barcode} bị trùng lặp', body['message'])

    def test_return400__duplicated_barcode_in_payload_of_multiple_skus_only_update(self):
        same_barcode = fake.text(30)
        self.__init_payload([[{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': fake.text(30), 'source': fake.text(255)}],
                             [{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': fake.text(30), 'source': fake.text(255)}]
                             ], number_skus=2, update_sku=True)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(f'barcode {same_barcode} bị trùng lặp', body['message'])

    def test_return400__duplicated_barcode_in_payload_of_multiple_skus_with_create_and_update(self):
        same_barcode = fake.text(30)
        self.__init_payload([[{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': fake.text(29), 'source': fake.text(255)}],
                             [{'barcode': same_barcode, 'source': fake.text(255)},
                              {'barcode': fake.text(29), 'source': fake.text(255)}]
                             ], number_skus=2)
        variant = fake.product_variant(product_id=self.product.id, uom_ratio_value=1)
        sku = fake.sellable_product(variant_id=variant.id, seller_id=self.category.seller_id, barcode=fake.text(30))
        fake.sellable_product_barcode(sku_id=sku.id, barcode=fake.text(25), is_default=True)
        barcodes = self.payload['variants'][0]['sku']['barcodes']
        self.payload['variants'][0].pop('sku')
        self.payload['variants'][0]['sku'] = {'sku': sku.sku,
                                              'barcodes': barcodes}

        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(f'barcode {same_barcode} bị trùng lặp', body['message'])

    def test_return400__duplicated_barcode_in_same_seller(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(f'barcode {barcodes_with_source[0][0].get("barcode")} của SKU {self.sku.seller_sku} đã tồn tại',
                         body['message'])

    def test_return400__update_with_duplicated_barcode_in_same_seller(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, update_sku=True)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(f'barcode {barcodes_with_source[0][0].get("barcode")} của SKU {self.sku.seller_sku} đã tồn tại',
                         body['message'])
