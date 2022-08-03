import json
import logging

from flask import current_app

from catalog.extensions.ram_queue_consumer import ProductDetail
from tests.catalog.api import APITestCase

from catalog import models

__author__ = 'long.t'

from tests.faker import fake

_logger = logging.getLogger(__name__)


class TestCreateListVariantsWithOrderedAttribute(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1076'
    FOLDER = '/Product/AdvancedInfo/Event'

    def setUp(self):
        self.skus = []
        attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(set_id=attribute_set.id)
        product = fake.product(attribute_set_id=attribute_set.id)
        attribute = fake.attribute(value_type='selection', group_ids=[attribute_group.id], is_variation=True)
        for i in range(0,10):
            option = fake.attribute_option(attribute_id=attribute.id)
            variant = fake.product_variant(product_id=product.id, attribute_set_id=attribute_set.id)
            fake.variant_attribute(variant_id=variant.id, attribute_id=attribute.id, option_id=option.id)
            sku = fake.sellable_product(variant_id=variant.id, attribute_set_id=attribute_set.id)
            self.skus.append(sku)
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def check_order(self):
        for sku in self.skus:
            product_group = models.db.session.\
                query(models.ProductDetailsV2).\
                filter(models.ProductDetailsV2.sku == sku.sku).\
                first().product_group

            product_group = json.loads(product_group)
            configurations = product_group.get('configurations')
            for configuration in configurations:
                options = configuration.get('options')
                list_check_options = []
                for option in options:
                    attribute_option = models.db.session.\
                        query(models.AttributeOption).\
                        filter(models.AttributeOption.id == option.get('option_id')).first()

                    list_check_options.append({'id': option.get('option_id'), 'priority': attribute_option.priority})
                if not all(list_check_options[i].get('priority') <= list_check_options[i+1].get('priority')
                           for i in range(len(list_check_options)-1)):
                    return False
        return True

    def get_product_detail_test_v2(self, session, message):
        data = json.loads(message)
        sku = data.get('sku')
        updated_by = data.get('updated_by')
        product_detail = ProductDetail(session)
        return product_detail.init_product_detail_v2(sku, updated_by)

    def test_create_list_sku__update_product_details_correct_order__with_ordered_attribute(self):
        for sku in self.skus:
            message = {
                'id': sku.id,
                'sku': sku.sku,
            }
            message = json.dumps(message)
            session = models.db.session
            sku_detail = self.get_product_detail_test_v2(session, message)
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
        self.assertTrue(self.check_order())
