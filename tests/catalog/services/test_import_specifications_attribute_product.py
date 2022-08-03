from tests.catalog.api import APITestCase
from catalog.biz.product_import.base import Importer
from tests.faker import fake


class TestImportSpecificationsAttributeProduct(APITestCase):
    ISSUE_KEY = 'SC-241'

    def setUp(self):
        self.variant = fake.product_variant()
        self.attributes = [fake.attribute(value_type='text')]
        self.row = {self.variant.code: 'Test'}

        self.importer = Importer(
            data=self.row,
            process=fake.file_import(),
            import_type=None
        )
        self.importer.variant = self.variant
        self.importer.specifications_attributes = self.attributes

    def test_attribute_type_text(self):
        rs = self.importer.import_variant_attributes()
        self.assertIsNone(rs)

    def test_attribute_type_selection(self):
        self.importer.specifications_attributes = [fake.attribute(value_type='selection')]
        rs = self.importer.import_variant_attributes()
        self.assertIsNone(rs)

    def test_attribute_type_multiple_select(self):
        self.importer.specifications_attributes = [fake.attribute(value_type='multiple_select')]
        rs = self.importer.import_variant_attributes()
        self.assertIsNone(rs)

    def test_attribute_type_selection_and_without_option(self):
        self.importer.specifications_attributes = [fake.attribute(value_type='selection')]
        rs = self.importer.import_variant_attributes()
        self.assertIsNone(rs)

    def test_attribute_type_selection_then_255(self):
        attribute = fake.attribute(value_type='selection')
        self.row.update({attribute.code: fake.text(256)})

        self.importer.row = self.row
        self.importer.specifications_attributes = [attribute]

        rs = self.importer.import_variant_attributes()
        self.assertIsNone(rs)

