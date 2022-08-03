# coding=utf-8
from sqlalchemy import (
    asc,
    desc,
    and_,
    or_,
    orm,
    func,
)
from sqlalchemy.orm import lazyload

from catalog import models
from catalog.extensions import exceptions as exc


class Singleton:
    instance = None

    def __new__(cls):
        raise NotImplementedError('This is singleton class')

    @classmethod
    def get_instance(cls):
        if cls.instance is None:
            cls.instance = object.__new__(cls)
        return cls.instance


class QueryBase:
    model = None
    obvious_not_found = None
    def __init__(self, query=None):
        self.obvious_not_found = False
        if query:
            self.query = query
        elif self.__class__.model:
            self.query = self.__class__.model.query

    def restrict_by_user(self, email, public_status=None):
        if self.obvious_not_found:
            return self

        if not public_status:
            public_status = tuple()
        if hasattr(self.__class__.model, 'created_by'):
            if hasattr(self.__class__.model, 'editing_status_code'):
                self.query = self.query.filter(or_(
                    self.__class__.model.created_by == email,
                    and_(
                        self.__class__.model.created_by != email,
                        self.__class__.model.editing_status_code.in_(public_status)
                    )
                ))
            else:
                self.query = self.query.filter(
                    self.__class__.model.created_by == email
                )
        return self

    def restrict_by_seller(self, seller_id, public_status=None):
        if self.obvious_not_found:
            return self

        if not public_status:
            public_status = tuple()
        if hasattr(self.__class__.model, 'seller_id'):
            if hasattr(self.__class__.model, 'editing_status_code'):
                self.query = self.query.filter(or_(
                    self.__class__.model.seller_id == seller_id,
                    and_(
                        self.__class__.model.seller_id != seller_id,
                        self.__class__.model.editing_status_code.in_(public_status)
                    )
                ))
            else:
                self.query = self.query.filter(
                    self.__class__.model.seller_id == seller_id
                )
        return self

    def pagination(self, page, page_size):
        if self.obvious_not_found:
            return self

        self.query = self.query.offset((page - 1) * page_size).limit(page_size)
        return self

    def __iter__(self):
        yield from self.query

    def __len__(self):
        if self.obvious_not_found:
            return 0

        count_query = self.query
        count_query = count_query.options(lazyload('*')).statement.with_only_columns([func.count()]).order_by(None)
        return models.db.session.execute(count_query).scalar()

    def get_query(self):
        return self.query

    def first(self):
        if self.obvious_not_found:
            return None

        return self.query.first()

    def all(self):
        if self.obvious_not_found:
            return []

        return self.query.all()

    def sort(self, sort_field, sort_order='ascend'):
        """sort

        :param sort_field:
        :param sort_order:
        """
        if self.obvious_not_found:
            return self

        cls = self.__class__
        if not hasattr(cls.model, sort_field):
            raise exc.BadRequestException(
                f'Không thể sắp xếp theo trường {sort_field}'
            )
        if sort_order not in ('ascend', 'descend'):
            raise exc.BadRequestException(
                f'Trường order chỉ nhận một trong 2 giá trị ascend hoặc descend'
            )
        sort_fn = asc if sort_order == 'ascend' else desc
        self.query = self.query.order_by(sort_fn(sort_field))
        return self

    def apply_filters(self, filters):
        """apply_filters

        :param filters:
        """
        raise NotImplementedError

    def load_fields(self, *fields):
        if self.obvious_not_found:
            return self

        self.query = self.query.options(
            orm.load_only(*fields)
        )
        return self

    def apply_like_conditions(self, filters, attr):
        if self.obvious_not_found:
            return

        if filters:
            value = filters.get(attr)
            if value:
                self.query = self.query.filter(
                    getattr(self.model, attr).like(f'%{value}%')
                )
