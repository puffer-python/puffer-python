import json
import logging
import random

from flask import current_app

import config
from catalog.extensions.ram_queue_consumer import ProductDetail
from tests.catalog.api import APITestCaseWithMysql
from sqlalchemy import text
from catalog import models as m

from catalog import models

__author__ = 'long.t'

from tests.faker import fake

_logger = logging.getLogger(__name__)


class TestUpdateVariantPackAttribute(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-1290'
    FOLDER = '/Product/AdvancedInfo/Event'

    def setUp(self):
        self.iam_user = fake.iam_user()
        self.skus = []
        attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(set_id=attribute_set.id)
        product = fake.product(attribute_set_id=attribute_set.id)
        self.attributes = []
        self.attributes.append(fake.attribute(code='pack_width', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='pack_length', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='pack_height', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='pack_weight', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='width', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='length', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='height', value_type='number', group_ids=[attribute_group.id]))
        self.attributes.append(fake.attribute(code='weight', value_type='number', group_ids=[attribute_group.id]))
        for i in range(0,10):
            variant = fake.product_variant(product_id=product.id, attribute_set_id=attribute_set.id)
            for attribute in self.attributes:
                if 'pack' not in attribute.code:
                    fake.variant_attribute(variant_id=variant.id, attribute_id=attribute.id)
            fake.variant_attribute(variant_id=variant.id, attribute_id=self.attributes[random.randint(0,3)].id)
            sku = fake.sellable_product(variant_id=variant.id, attribute_set_id=attribute_set.id)
            self.skus.append(sku)
        m.db.session.add(self.skus[0])
        m.db.session.commit()
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def url(self):
        return '/variants/attributes'

    def method(self):
        return 'post'

    def _get_product_detail_test_v2(self, session, message):
        data = json.loads(message)
        sku = data.get('sku')
        updated_by = data.get('updated_by')
        product_detail = ProductDetail(session)
        return product_detail.init_product_detail_v2(sku, updated_by)

    def test_update_product_details_v2_with_pack_attributes(self):
        for sku in self.skus:
            message = {
                'id': sku.id,
                'sku': sku.sku,
            }
            message = json.dumps(message)
            session = models.db.session
            sku_detail = self._get_product_detail_test_v2(session, message)
            if sku_detail:
                exist = session.query(models.ProductDetailsV2).filter(
                    models.ProductDetailsV2.sku == sku_detail.get('sku')).first()
                if exist:
                    for k, v in sku_detail.items():
                        setattr(exist, k, v)
                else:
                    sku_detail['created_by'] = sku_detail['updated_by']
                    model = models.ProductDetailsV2(**sku_detail)
                    session.add(model)
            product_details_v2 = m.db.session.query(m.ProductDetailsV2).filter(m.ProductDetailsV2.sku == sku.sku).first()
            attributes = json.loads(product_details_v2.attributes)
            for pack_attribute in attributes:
                if 'pack' in pack_attribute.get('code') and not pack_attribute.get('values')[0].get('value'):
                    for attribute in attributes:
                        if attribute.get('code') == pack_attribute.get('code').replace("pack_", ""):
                            assert pack_attribute.get('values')[0].get('value') == attribute.get('values')[0].get('value')

