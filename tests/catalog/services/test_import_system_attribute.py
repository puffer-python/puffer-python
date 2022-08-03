from tests.catalog.api import APITestCase
from tests.faker import fake


class TestImportSystemAttribute(APITestCase):
    ISSUE_KEY = 'CATALOGUE-37'

    def testGetAttributeIsSystem(self):
        attribute_set = fake.attribute_set()
        group_attribute = fake.attribute_group(
            set_id=0,
            system_group=True
        )
        fake.attribute(
            group_ids=[group_attribute.id]
        )

        specifications_attributes = attribute_set.get_specifications_attributes()
        self.assertIsNotNone(specifications_attributes)

    def testGetAttributeIsSystemCheckHasAttribute(self):
        attribute_set = fake.attribute_set()
        group_attribute = fake.attribute_group(
            set_id=attribute_set.id,
            system_group=True
        )
        attribute = fake.attribute(
            group_ids=[group_attribute.id],
            is_variation=False
        )

        specifications_attributes = attribute_set.get_specifications_attributes()
        self.assertEqual(attribute, specifications_attributes[0])

    def testGetAttributeIsSystemGroupCheckNot(self):
        attribute_set = fake.attribute_set()
        group_attribute = fake.attribute_group(
            set_id=99,
            system_group=False
        )
        attribute = fake.attribute(
            group_ids=[group_attribute.id]
        )

        specifications_attributes = attribute_set.get_specifications_attributes()
        self.assertListEqual(specifications_attributes, [])
