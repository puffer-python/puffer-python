#coding=utf-8

from sqlalchemy import or_
from catalog.services import QueryBase
from catalog import models


class SaleCategoryQuery(QueryBase):
    model = models.SaleCategory

    def apply_filters(self, filters):
        query = filters.get('query')
        if query:
            self.query = self.query.filter(or_(
                self.model.name.like(f'%{query}%')
            ))
        level = filters.get('level')
        if level:
            self.query = self.query.filter(
                self.model.depth == level
            )
        parent_id = filters.get('parent_id')
        if parent_id:
            self.query = self.query.filter(
                self.model.parent_id == parent_id
            )
