# coding=utf-8

from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from catalog.services import QueryBase
from catalog import models


class CategoryQuery(QueryBase):
    model = models.Category

    def all(self):
        return self.query.options(
            joinedload('parent'),
            joinedload('attribute_set')
        ).all()

    def apply_filters(self, filters):
        id = filters.get('id')
        if id:
            self.query = self.query.filter(
                self.__class__.model.id == id
            )

        ids = filters.get('ids')
        if ids:
            self.query = self.query.filter(
                self.__class__.model.id.in_(ids)
            )

        depth = filters.get('depth')
        if depth is not None:
            self.query = self.query.filter(
                models.Category.depth == depth
            )

        query = filters.get('query')
        if query is not None:
            self.query = self.query.filter(or_(
                models.Category.name.like(f'%{query}%'),
                models.Category.code.like(f'%{query}%')
            ))

        id = filters.get('id')
        if id is not None:
            self.query = self.query.filter(
                models.Category.id == id
            )

        codes = filters.get('codes')
        if codes:
            self.query = self.query.filter(
                models.Category.code.in_(codes.split(','))
            )

        parent_id = filters.get('parent_id')
        if parent_id is not None:
            self.query = self.query.filter(
                models.Category.parent_id == parent_id
            )

        is_active = filters.get('is_active')
        if is_active is not None:
            self.query = self.query.filter(
                models.Category.is_active == is_active
            )

        seller_ids = filters.get('seller_ids')
        if seller_ids and seller_ids != '0':
            if isinstance(seller_ids, str):
                seller_ids = list(map(lambda x: int(x), filter(lambda n: n.isnumeric(), seller_ids.split(","))))
            elif isinstance(seller_ids, int):
                seller_ids = [seller_ids]
            else:
                seller_ids = list(seller_ids)

            self.query = self.query.filter(
                self.__class__.model.seller_id.in_(seller_ids)
            )

        return self


class CategoryRepository:
    @staticmethod
    def transaction_insert(data):
        category = models.Category(**data)
        models.db.session.add(category)
        models.db.session.flush()
        return category

    @staticmethod
    def get_by_id(category_id):
        return models.Category.query.get(category_id)

    @staticmethod
    def get_all_by_path(path):
        category_ids = path.split("/")
        return models.Category.query.filter(models.Category.id.in_(category_ids)).all()


class ProductCategoryQuery(QueryBase):
    model = models.ProductCategory

    def apply_filter(self, **kwargs):
        product_ids = kwargs.get('product_ids')
        if product_ids:
            self._apply_product_ids_filter(product_ids)

        seller_ids = kwargs.get('seller_ids')
        if seller_ids:
            self._apply_seller_ids_filter(seller_ids)

    def _apply_product_ids_filter(self, product_ids):
        self.query = self.query.filter(models.ProductCategory.product_id.in_(product_ids))

    def _apply_seller_ids_filter(self, seller_ids):
        self.query = self.query.filter(
            models.ProductCategory.category_id == models.Category.id,
            models.Category.seller_id.in_(seller_ids)
        )