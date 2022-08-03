from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog import models as m
from catalog.services.attribute_sets import AttributeSetService


service = AttributeSetService.get_instance()

class TestAttributeSetCreateVariation(APITestCase):
    ISSUE_KEY = 'SC-324'

    def setUp(self):
        super().setUp()
        self.attribute_set = fake.attribute_set()
        self.groups = [fake.attribute_group(set_id=self.attribute_set.id) for _ in range(3)]
        self.attrs = [fake.attribute(group_ids=[group.id for group in self.groups]) for _ in range(5)]

    def _check_variation_priority(self, attribute_set_id):
        instances = m.AttributeGroupAttribute.query.join(m.AttributeGroup).join(m.AttributeSet).filter(
            m.AttributeSet.id == attribute_set_id,
            m.AttributeGroupAttribute.is_variation == 1
        ).all()
        priorities = [instance.variation_priority for instance in instances]
        assert len(set(priorities)) == len(instances)
        priorities = sorted(priorities)
        for i in range(1, len(priorities)):
            assert priorities[i] - 1 == priorities[i-1]


    def test_create_success(self):
        for i in range(5):
            variation_display_type = fake.random_element(('code', 'text', 'image'))
            ret = service.create_attribute_variation(self.attribute_set.id,
                                             self.attrs[i].id,
                                             variation_display_type)
            assert self.attrs[i].id == ret.attribute_id
            assert ret.is_variation == 1
            assert ret.variation_display_type == variation_display_type
            self._check_variation_priority(self.attribute_set.id)
