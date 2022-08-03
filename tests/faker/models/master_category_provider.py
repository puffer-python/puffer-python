# coding=utf-8
import logging
import faker.providers
from tests.faker import fake

from catalog.models import (
    db,
    MasterCategory,
)

__author__ = 'Thanh.NK'
_logger = logging.getLogger(__name__)


class MasterCategoryProvider(faker.providers.BaseProvider):
    def master_category(self, code=None, name=None, is_active=None,
                        parent_id=None, tax_in_code=None, tax_out_code=None,
                        attribute_set_id=None, seller_id=None):
        ret = MasterCategory()
        ret.code = code if code else fake.unique_str(3)
        ret.name = name if name else fake.name()
        ret.is_active = True if is_active is None else is_active
        ret.parent_id = 0 if parent_id is None else parent_id
        ret.attribute_set_id = attribute_set_id if attribute_set_id else fake.attribute_set().id
        tax = fake.tax()
        ret.tax_in_code = tax_in_code if tax_in_code else tax.code
        ret.tax_out_code = tax_out_code if tax_out_code else tax.code
        ret.manage_serial = fake.boolean()
        if ret.manage_serial:
            ret.auto_generate_serial = fake.boolean()
        db.session.add(ret)
        db.session.flush()
        if ret.parent:
            ret.path = ret.parent.path  + '/' + str(ret.id)
        else:
            ret.path = str(ret.id)
        ret.depth = len(ret.path.split('/'))
        return ret
