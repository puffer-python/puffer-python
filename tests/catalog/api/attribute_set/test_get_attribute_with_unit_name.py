import random

import config
import logging

from catalog.models import db
from tests.faker import fake
from tests.catalog.api import APITestCase

__author__ = 'thanh.nh'
_logger = logging.getLogger(__name__)


class GetAttributeWithUnitName(APITestCase):
    ISSUE_KEY = 'CATALOGUE-991'
    FOLDER = '/AttributeSet/Get/UnitPostfix'

    def setUp(self):
        super().setUp()
        self.seller_id = fake.integer()
        self.attribute_set = fake.attribute_set()
        self.attribute_groups = [
            fake.attribute_group(
                set_id=self.attribute_set.id,
                system_group=False,
            )
            for _ in range(2)
        ]
        group_ids = [
            group.id
            for group in self.attribute_groups
        ]
        # create fake dimensional attributes
        self.attributes = [
            fake.attribute(
                group_ids=group_ids,

            )

        ]
        # create normal attributes
        self.attributes.extend(
            fake.attribute(group_ids=group_ids)
            for _ in range(3)
        )

    def url(self):
        return f'/attribute_sets/{self.attribute_set.id}'

    def method(self):
        return 'GET'

    def headers(self):
        return {
            'X-Seller-id': self.seller_id,
            'Host': config.INTERNAL_HOST_URLS[0]
        }

    def test_suffix_return200_withData(self):
        suffix = fake.text()
        choice_attribute = random.choice(self.attributes)
        choice_attribute.suffix = suffix
        db.session.commit()

        code, body = self.call_api()
        assert code == 200
        checked = 0

        for attribute in body['result']['attributes']:
            if choice_attribute.id == attribute.get('id'):
                checked = checked + 1
                self.assertEqual(attribute.get('name'),
                                 '{} ({})'.format(choice_attribute.name, suffix))
        self.assertGreater(checked, 0)

    def test_non_suffix_return200_withData(self):
        choice_attribute = random.choice(self.attributes)
        choice_attribute.suffix = None
        db.session.commit()
        code, body = self.call_api()
        assert code == 200

        checked = 0
        for attribute in body['result']['attributes']:
            if choice_attribute.id == attribute.get('id'):
                checked = checked + 1
                self.assertEqual(attribute.get('name'), choice_attribute.name)
        self.assertGreater(checked, 0)
