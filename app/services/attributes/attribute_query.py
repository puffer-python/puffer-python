# coding=utf-8

from sqlalchemy import or_
from catalog import models
from catalog.services import QueryBase


class AttributeQuery(QueryBase):
    def __init__(self):
        self.query = models.Attribute.query.filter(
            models.Attribute.code.notin_(['uom', 'uom_ratio'])
        )

    def apply_filters(self, filters):
        if filters.get('codes'):
            self.query.filter(
                models.Attribute.code.in_(filters['codes'])
            )

        if filters.get('query'):
            self._apply_query(filters['query'])

        if isinstance(filters.get('value_type'), str):
            self.query = self.query.filter(
                models.Attribute.value_type.in_(
                    filters['value_type'].split(',')
                )
            )

        if isinstance(filters.get('is_required'), int):
            self.query = self.query.filter(
                models.Attribute.is_required == filters['is_required']
            )

        if isinstance(filters.get('is_searchable'), int):
            self.query = self.query.filter(
                models.Attribute.is_searchable == filters['is_searchable']
            )

        if isinstance(filters.get('is_filterable'), int):
            self.query = self.query.filter(
                models.Attribute.is_filterable == filters['is_filterable']
            )

        if isinstance(filters.get('is_comparable'), int):
            self.query = self.query.filter(
                models.Attribute.is_comparable == filters['is_comparable']
            )

    def _apply_query(self, query):
        if isinstance(query, str):
            _like_expr = '%{}%'.format(query)
            self.query = self.query.filter(
                or_(
                    models.Attribute.name.like(_like_expr),
                    models.Attribute.code.like(_like_expr)
                )
            )
