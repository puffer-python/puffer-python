from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.attribute_sets import AttributeSetService


service = AttributeSetService.get_instance()


class TestAttributeSetGetAttribute(APITestCase):
    ISSUE_KEY = 'SC-245'

    def setUp(self):
        super().setUp()
        group = fake.attribute_group(set_id=1)
        fake.attribute(group_ids=[group.id])

    def test_service(self):
        data = service.get_attributes(1)
        self.assertEqual(isinstance(data, list), True)
        self.assertEqual(len(data), 1)

    def test_service_not_found(self):
        data = service.get_attributes(2)
        self.assertEqual(len(data), 0)
