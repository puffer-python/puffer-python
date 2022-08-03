# coding=utf-8

from sqlalchemy import or_

from catalog import models
from catalog.services import QueryBase


class AttributeSetListQuery(QueryBase):
    """
    Query danh sách nhóm thuộc tính theo 1 loạt các filter
    """
    model = models.AttributeSet

    def apply_filters(self, filters):
        query = filters.get('query')
        if query:
            self.query = self.query.filter(or_(
                models.AttributeSet.name.like(f'%{query}%'),
                models.AttributeSet.code.like(f'%{query}%'),
            ))
