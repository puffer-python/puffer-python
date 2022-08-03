# coding=utf-8

from sqlalchemy import or_
from catalog.services import QueryBase
from catalog import models


class ShippingTypeQuery(QueryBase):
    model = models.ShippingType

    def apply_filters(self, filters):
        self.apply_like_conditions(filters, 'name')
        self.apply_like_conditions(filters, 'code')
        value = filters.get('query')
        if value:
            self.query = self.query.filter(or_(
                getattr(self.model, 'name').like(f'%{value}%'),
                getattr(self.model, 'code').like(f'%{value}%')
            ))
