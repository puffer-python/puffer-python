# coding=utf-8
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from catalog.services import QueryBase
from catalog import models
from catalog import utils


class MasterCategoryQuery(QueryBase):
    model = models.MasterCategory

    def all(self):
        return self.query.options(
            joinedload('parent'),
            joinedload('tax_in'),
            joinedload('tax_out'),
            joinedload('attribute_set'),
        ).all()

    def apply_filters(self, filters):
        query = filters.get('query')
        if query:
            self.query = self.query.filter(
                or_(
                    models.MasterCategory.name.like(f'%{utils.remove_accents(query)}%'),
                    models.MasterCategory.name_ascii.like(f'%{utils.remove_accents(query)}%'),
                    models.MasterCategory.code.like(f'%{query}%')
                )
            )
        level = filters.get('level')
        if level:
            self.query = self.query.filter(
                models.MasterCategory.depth == level
            )
        parent_id = filters.get('parent_id')
        if parent_id:
            self.query = self.query.filter(
                models.MasterCategory.parent_id == parent_id
            )
        id = filters.get('id')
        if id:
            self.query = self.query.filter(
                models.MasterCategory.id == id
            )
        is_active = filters.get('is_active')
        if is_active is not None:
            self.query = self.query.filter(
                models.MasterCategory.is_active.is_(is_active)
            )
        return self
