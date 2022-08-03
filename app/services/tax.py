#coding=utf-8

from catalog.services import (
    Singleton,
    QueryBase,
)
from catalog import models


class TaxQuery(QueryBase):
    model = models.Tax


class TaxService(Singleton):
    def get_taxes_list(self):
        query = TaxQuery()
        return query.all()
