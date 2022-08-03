# coding=utf-8
import logging
import faker.providers
from flask_login import current_user

from tests.faker import fake

from catalog import models as m

__author__ = 'Thanh.NK'
_logger = logging.getLogger(__name__)


class CategoryProvider(faker.providers.BaseProvider):
    def category(self, name=None, seller_id=None, is_active=None, parent_id=None, manage_serial=None,
                 attribute_set_id=None, is_adult=None, **kwargs):
        ret = m.Category()
        ret.seller_id = seller_id or fake.seller().id
        ret.code = kwargs.get('code') or fake.unique_str(6)
        ret.name = name if name is not None else fake.unique_str(6)
        ret.parent_id = parent_id or 0
        ret.manage_serial = manage_serial if manage_serial is not None else True
        ret.auto_generate_serial = fake.boolean() if ret.manage_serial else None
        ret.attribute_set_id = attribute_set_id or fake.attribute_set().id
        ret.is_active = is_active if is_active is not None else True
        ret.tax_in_code = fake.unique_str(6)
        ret.tax_out_code = fake.unique_str(6)
        ret.unit_id = kwargs.get('unit_id') or fake.unit().id

        if is_adult is not None:
            ret.is_adult = is_adult

        m.db.session.add(ret)
        m.db.session.flush()
        ret.path = gen_path(ret)
        ret.depth = len(ret.path.split('/'))
        ret.master_category_id = kwargs.get('master_category_id', None)
        ret.master_category = kwargs.get('master_category', None)
        m.db.session.commit()

        return ret

    def category_json(self, **kwargs):
        category = m.Category(**kwargs)
        m.db.session.add(category)
        m.db.session.commit()
        return category


def gen_path(category):
    if category.parent_id not in [None, 0]:
        parent = m.Category.query.filter(
            m.Category.id == category.parent_id
        ).first()
        return '{}/{}'.format(parent.path, category.id)
    return str(category.id)
