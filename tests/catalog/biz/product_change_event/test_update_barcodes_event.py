# coding=utf-8
import logging
import json
import time
from datetime import timedelta

from catalog import models as m
from sqlalchemy.orm import sessionmaker

from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog import utils
import random
from catalog.extensions.ram_queue_consumer import process_update_product_detail_v2, process_update_product_detail


__author__ = 'long.t'
_logger = logging.getLogger(__name__)

__Session = sessionmaker(bind=m.db.engine)

class TestUpdateProductDetailBarcodes(APITestCase):

    ISSUE_KEY = "CATALOGUE-1109"
    FOLDER = "Product/Barcodes/Event"

    def setUp(self):
        self.created_by = 'longt'
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.product = fake.product(category_id=self.category.id,
                                    master_category_id=self.master_category.id,
                                    created_by=self.created_by)
        self.product_category = fake.product_category(
            product_id=self.product.id,
            category_id=self.category.id
        )

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

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
            'attributeSetId': self.product.attribute_set_id,
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

    def test_return_update_productdetailv1_success_with_update_sku_barcode(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, same_barcode=False,
                                                                        update_sku=True)
        code, body = self.call_api(self.payload)
        ram_event = m.db.session.query(m.RamEvent).all()
        self.assertEqual(200, code)
        self.assertTrue(len(ram_event))

    def test_return_update_productdetailv2_success_with_update_sku_barcode(self):
        barcodes_with_source = self.__init_payload_with_new_sku_barcode(add_new_seller=False, same_barcode=False,
                                                                        update_sku=True)
        code, body = self.call_api(self.payload)
        ram_event = m.db.session.query(m.RamEvent).all()
        self.assertEqual(200, code)
        self.assertTrue(len(ram_event))
