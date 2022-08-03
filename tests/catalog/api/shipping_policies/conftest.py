# coding=utf-8
import logging

__author__ = 'Kien.HT'

import pytest

from tests.faker import fake

_logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def seed_shipping_policy_misc_data(session):
    for code in ['all', 'bulky', 'near']:
        fake.misc(data_type='shipping_type', code=code)
