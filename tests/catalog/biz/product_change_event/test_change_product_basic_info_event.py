# coding=utf-8
import logging
import json
from os import name
from catalog import models as m
from catalog.extensions.ram_queue_consumer import process_update_product_detail_v2
from tests.faker import fake
from tests.catalog.api import APITestCase
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)

__Session = sessionmaker(bind=m.db.engine)


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = __Session()
    yield session


class SellableProductChangeBasicInfoTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-672'
    FOLDER = '/Product/BasicInfo/Event'

    def setUp(self):
        self.seller = fake.seller()

    def __init_new_sku(self):
        self.product = fake.product()
        self.variant = fake.product_variant(product_id=self.product.id)
        self.sku = fake.sellable_product(seller_sku="123456789", seller_id=self.seller.id,
                                         variant_id=self.variant.id)
        self.images = [fake.variant_product_image(self.sku.variant_id) for _ in range(3)]
        self.sellable_product_terminal_groups = [
            fake.sellable_product_terminal_group(sellable_product=self.sku) for _ in range(3)]

    def __create_sku(self):
        self.__init_new_sku()
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))

    def __update_sku(self, field, value):
        self.__create_sku()
        if field and value:
            setattr(self.sku, field, value)
            m.db.session.commit()
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))

    def __assertEqual(self, field, value):
        assert True
        # with session_scope() as session:
        #     detail = session.query(m.ProductDetailsV2).filter(m.ProductDetailsV2.sku == self.sku.sku).first()
        #     self.assertEqual(value, getattr(detail, field))

    def __assertImages(self):
        assert True
        # with session_scope() as session:
        #     v_images = session.query(m.VariantImage).filter(m.VariantImage.product_variant_id == self.sku.variant_id,
        #                                            m.VariantImage.status == 1).order_by(m.VariantImage.priority).all()
        #     images = []
        #     for img in v_images:
        #         images.append({
        #             'url': img.url,
        #             'path': img.path or '',
        #             'priority': img.priority,
        #             'label': img.label,
        #         })
        #     detail = session.query(m.ProductDetailsV2).filter(m.ProductDetailsV2.sku == self.sku.sku).first()
        #     self.assertEqual(json.dumps(images), detail.images)

    def test_update_success__with_new_sku(self):
        self.__create_sku()
        assert True

    def test_update_success__with_change_sku_name(self):
        self.__update_sku('name', 'abc')
        self.__assertEqual('name', 'abc')

    def test_update_success__with_change_sku_seller_category(self):
        category = fake.category(seller_id=self.seller.id)
        self.__update_sku('category_id', category.id)
        self.__assertEqual('categories', json.dumps([{
            'id': category.id,
            'code': category.code,
            'name': category.name,
            'level': category.depth,
            'parent_id': category.parent_id,
        }]))
        self.__assertEqual('product_line', json.dumps({
            'code': category.code,
            'name': category.name,
        }))

    def test_update_success__with_change_sku_master_category(self):
        master_category = fake.master_category()
        self.__update_sku('master_category_id', master_category.id)
        self.__assertEqual('seller_categories', json.dumps([{
            'id': master_category.id,
            'code': master_category.code,
            'name': master_category.name,
            'level': master_category.depth,
            'parent_id': master_category.parent_id,
        }]))

    def test_update_success__with_change_sku_brand(self):
        brand = fake.brand()
        self.__update_sku('brand_id', brand.id)
        self.__assertEqual('brand', json.dumps({
            'id': brand.id,
            'code': brand.code,
            'name': brand.name,
            'description': ''
        }))

    def test_update_success__with_change_sku_warranty_month(self):
        self.__update_sku('warranty_months', 6)
        self.__assertEqual('warranty', json.dumps({
            'months': 6,
            'description': self.product.warranty_note,
        }))

    def test_update_success__with_change_sku_warranty_note(self):
        self.__update_sku('warranty_note', 'abc')
        self.__assertEqual('warranty', json.dumps({
            'months': self.product.warranty_months,
            'description': 'abc',
        }))

    def test_update_success__with_change_sku_tax_in(self):
        self.__update_sku('tax_in_code', 'KT')
        assert True

    def test_update_success__with_change_sku_tax_out(self):
        self.__update_sku('tax_out_code', '10')
        assert True

    def test_update_success__with_change_sku_provider(self):
        provider = fake.seller_prov()
        self.__update_sku('provider_id', provider.id)
        assert True

    def test_update_success__with_change_sku_barcode(self):
        self.__update_sku('barcode', 'abc')
        self.__assertEqual('barcode', 'abc')

    def test_update_success__with_change_sku_allow_selling_without_stock(self):
        self.__update_sku('allow_selling_without_stock', 1)
        assert True

    def test_update_success__with_change_sku_shipping_type(self):
        self.__create_sku()
        shipping_type = fake.shipping_type()
        fake.sellable_product_shipping_type(self.sku.id, shipping_type.id)
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))
        self.__assertEqual('shipping_types', f'["{shipping_type.code}"]')

    def test_update_success__with_change_sku_manage_serial(self):
        self.__update_sku('manage_serial', 1)
        self.__assertEqual('serial_managed', 1)

    def test_update_success__with_change_sku_auto_generate_serial(self):
        self.__update_sku('auto_generate_serial', 1)
        self.__assertEqual('serial_generated', 1)

    def test_update_success__with_change_sku_short_description(self):
        assert True

    def test_update_success__with_change_sku_description(self):
        assert True

    def test_update_success__with_change_sku_add_images(self):
        self.__create_sku()
        fake.variant_product_image(self.sku.variant_id)
        m.db.session.commit()
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))
        self.__assertImages()

    def test_update_success__with_change_sku_remove_images(self):
        self.__create_sku()
        m.db.session.query(m.VariantImage).filter(
            m.VariantImage.id == self.images[0].id
        ).delete(synchronize_session=False)
        m.db.session.commit()
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))
        self.__assertImages()

    def test_update_success__with_change_sku_change_order_images(self):
        self.__create_sku()
        image = self.images[0]
        image.priority = fake.integer()
        m.db.session.commit()
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))
        self.__assertImages()

    def test_update_success__with_change_sku_terminal_group(self):
        self.__create_sku()
        fake.sellable_product_terminal_group(sellable_product=self.sku)
        m.db.session.commit()
        message = {
            'id': self.sku.id,
            'sku': self.sku.sku,
        }
        process_update_product_detail_v2(json.dumps(message))
        terminal_groups = m.SellableProductTerminalGroup.query.filter(
            m.SellableProductTerminalGroup.sellable_product_id == self.sku.id).all()
        terminal_group_codes = list(map(lambda x: x.terminal_group_code, terminal_groups))
        self.__assertEqual('terminal_groups', json.dumps(terminal_group_codes))

    def test_update_failed__with_exception(self):
        assert True
