# coding=utf-8
import logging

__author__ = 'Kien.HT'

import random

from catalog import models as m
from faker.providers import BaseProvider

from tests.faker import fake

_logger = logging.getLogger(__name__)


class ShippingPolicyProvider(BaseProvider):
    def shipping_policy(self, name=None, is_active=None, shipping_type=None,
                        category_ids=[], provider_ids=[]):
        policy = m.ShippingPolicy()
        policy.name = name or fake.text(length=100)
        policy.is_active = is_active if is_active is not None else True

        for code in ['all', 'near', 'bulky']:
            fake.misc(data_type='shipping_policy', code=code)
        policy.shipping_type = shipping_type or random.choice(['all', 'near', 'bulky'])
        m.db.session.add(policy)
        m.db.session.flush()

        provider_ids = provider_ids or [fake.seller_prov().id for _ in range(3)]
        for provider_id in provider_ids:
            for category_id in category_ids:
                mapping = m.ShippingPolicyMapping()
                mapping.policy_id = policy.id
                mapping.provider_id = provider_id
                mapping.category_id = category_id
                m.db.session.add(mapping)

        m.db.session.commit()
        return policy
