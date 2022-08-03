# coding=utf-8
import logging
import queue
import re
import os

from flask_login import current_user
from sqlalchemy import or_, func
import sqlalchemy as sa

from catalog import models as m
from catalog import utils
from catalog.services import Singleton
from .query import MasterCategoryQuery

__author__ = 'Thanh.NK'
__logger__ = logging.getLogger(__name__)


class MasterCategoryService(Singleton):
    def get_master_category_list(self, filters, page, page_size):
        """Get list sale_category
        """
        query = MasterCategoryQuery()
        query.apply_filters(filters)
        total_records = len(query)
        query.pagination(page, page_size)
        return query.all(), total_records

    def get_master_category_tree(self, master_category_id):
        query = MasterCategoryQuery()
        root = query.apply_filters({'id': master_category_id}).first()
        if not root:
            return None
        all_nodes = m.MasterCategory.query.filter(
            or_(
                m.MasterCategory.path.like(f'{root.id}/%'),
                m.MasterCategory.path.like(f'%/{root.id}/%'),
            ),
            m.MasterCategory.is_active.is_(True)
        ).all()
        all_nodes.append(root)
        for node in all_nodes:
            children = list(filter(lambda x: x.parent_id == node.id, all_nodes))
            if len(children) > 0:
                setattr(node, "_children", children)
        return root

    def create_master_category(self, data):
        category = m.MasterCategory(**data)
        m.db.session.add(category)
        m.db.session.flush()
        if category.parent_id:
            category.path = category.parent.path + '/' + str(category.id)
            category.depth = category.parent.depth + 1
        else:
            category.path = str(category.id)
            category.depth = 1
        m.db.session.commit()
        return category

    def update_master_category(self, cat_id, data):
        category = m.MasterCategory.query.get(cat_id)
        parent_id = data.pop('parent_id', None)
        for k, v in data.items():
            if hasattr(category, k):
                setattr(category, k, v)
        all_node = m.MasterCategory.query.filter(or_(
            m.MasterCategory.path.like(f'{cat_id}/%'),
            m.MasterCategory.path.like(f'%/{cat_id}/%'),
        ))

        if parent_id is not None:
            category.parent_id = parent_id
            m.db.session.flush()
            if category.parent_id == 0:
                category.path = str(category.id)
            else:
                category.path = category.parent.path + '/' + str(category.id)
            category.depth = len(category.path.split('/'))
            for node in all_node:
                node.path = node.parent.path + '/' + str(node.id)
                node.depth = len(node.path.split('/'))

        m.db.session.commit()
        return category

    def get_master_category(self, cat_id):
        return m.MasterCategory.query.get(cat_id)

    def get_recommendation_category(self, name, limit, **kwargs):
        master_categories = m.MasterCategory.query.filter(
            m.MasterCategory.is_active == 1
        ).all()
        import Levenshtein
        master_categories = sorted(
            master_categories,
            key=lambda x: Levenshtein.distance(x.name, name),
        )

        return master_categories[:limit]
