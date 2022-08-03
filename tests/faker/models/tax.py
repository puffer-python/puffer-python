#coding=utf-8

from faker.providers import BaseProvider
from tests.faker import fake
from catalog.models import (
    db,
    Tax,
)

class TaxProvider(BaseProvider):
    def tax(self, code=None, amount=None, label=None):
        ret = Tax(
            code=code or fake.text(5),
            amount=amount or fake.float(100),
            label=label or fake.text(5)
        )
        db.session.add(ret)
        db.session.commit()
        return ret
