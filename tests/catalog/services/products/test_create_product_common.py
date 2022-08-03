#coding=utf-8
import copy

from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from catalog import utils
from catalog.services.products.product import ProductService
from tests import logged_in_user


service = ProductService.get_instance()


class CreateProductCommonServiceTestCase(APITestCase):
    # ISSUE_KEY = 'SC-339'
    ISSUE_KEY = 'SC-550'

    def setUp(self):
        self.user = fake.iam_user()
        self.data = {
            'name': fake.name(),
            'is_bundle': False,
            'master_category_id': fake.master_category(is_active=True).id,
            'category_id': fake.category().id,
            'attribute_set_id': fake.attribute_set().id,
            'tax_in_code': fake.tax().code,
            'tax_out_code': fake.tax().code,
            'type': fake.misc(data_type='product_type', code=fake.text(5)).code,
            'is_physical': fake.random_element((True, False)),
            'brand_id': fake.brand(is_active=True).id,
            'warranty_months': fake.integer(),
            'warranty_note': fake.text(),
            'unit_id': fake.unit().id,
            'unit_po_id': fake.unit().id,
            'model': fake.text(),
            'detailed_description': fake.text(),
            'description': fake.text()
        }
        self.user = fake.iam_user(seller_id=fake.seller().id)

    def assertBody(self, data, product):
        for key, value in data.items():
            if hasattr(product, key):
                assert getattr(product, key) == value
        assert product.url_key == utils.slugify(product.name)
        assert product.created_at

    def test_passValidData__returnSavedProduct(self):
        product = service.create_product(self.data, self.user.email)
        self.assertBody(self.data, product)
        self.assertEqual(True, product.spu.startswith('SPU') \
                         and len(product.spu) == 13)
        assert product.created_by == self.user.email

    def test_notPassing_unitId_returnSavedProduct(self):
        data = copy.deepcopy(self.data)
        del data['unit_id']
        del data['unit_po_id']
        product = service.create_product(self.data, self.user.email)
        self.assertBody(self.data, product)
        self.assertEqual(True, product.spu.startswith('SPU') \
                         and len(product.spu) == 13)
        assert product.created_by == self.user.email

    def test_notPassing_taxOutCode_returnSavedProduct(self):
        data = copy.deepcopy(self.data)
        del data['unit_id']
        del data['unit_po_id']
        product = service.create_product(data, self.user.email)
        self.assertBody(data, product)
        self.assertEqual(True, product.spu.startswith('SPU') \
                         and len(product.spu) == 13)
        assert product.created_by == self.user.email