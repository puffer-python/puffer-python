#coding=utf-8

from sqlalchemy import (
    or_,
)

from catalog import models as m
from catalog.services import QueryBase


class ProductQuery(QueryBase):
    model = m.Product

    def apply_filters(self, filters):
        if filters.get('seller_id'):
            seller_id = filters.get('seller_id')
            subquery = m.db.session.query(m.Product.id).join(
                m.SellableProduct,
                m.SellableProduct.product_id == m.Product.id).filter(
                    m.SellableProduct.seller_id == seller_id
                ).group_by(m.Product.id)
            self.query = self.query.filter(m.Product.id.in_(subquery.subquery()))
        id_ = filters.get('id')
        if id_ is not None:
            if isinstance(id_, int):
                self.query = self.query.filter(
                    m.Product.id == id_
                )
            else:
                ids = list(map(int, id_.split(',')))
                self.query.filter(
                    m.Product.id.in_(ids)
                )
        spu = filters.get('spu')
        if spu is not None:
            self.query = self.query.filter(
                m.Product.spu.like(f'%{spu}%')
            )
        master_category_id = filters.get('master_category_id')
        if master_category_id is not None:
            master_category_ids = list(map(int, master_category_id.split(',')))
            self.query = self.query.filter(
                m.Product.master_category_id.in_(master_category_ids)
            )
        attribute_set_id = filters.get('attribute_set_id')
        if attribute_set_id is not None:
            attribute_set_ids = list(map(int, attribute_set_id.split(',')))
            self.query = self.query.filter(
                m.Product.attribute_set_id.in_(attribute_set_ids)
            )
        brand_id = filters.get('brand_id')
        if brand_id is not None:
            brand_ids = list(map(int, brand_id.split(',')))
            self.query = self.query.filter(
                m.Product.brand_id.in_(brand_ids)
            )

        brand_ids = filters.get('brand_ids')
        if brand_ids:
            self.query = self.query.filter(
               m.Product.brand_id.in_(brand_ids)
            )

        name = filters.get('name') or filters.get('keyword')
        if name is not None:
            self.query = self.query.filter(
                m.Product.name.like(f'%{name}%')
            )
        model = filters.get('model')
        if model is not None:
            self.query = self.query.filter(
                m.Product.model.like(f'%{model}%')
            )

        models = filters.get('models')
        if models:
            self.query  = self.query.filter(
                m.Product.model.in_(models)
            )
        type_ = filters.get('type')
        if type_ is not None:
            self.query = self.query.filter(
                m.Product.type == type_
            )
        tax_id = filters.get('tax_id')
        if tax_id is not None:
            self.query = self.query.filter(
                m.Product.tax_id == tax_id
            )
        editing_status_code = filters.get('editing_status_code')
        if editing_status_code:
            self.query = self.query.filter(
                self.__class__.model.editing_status_code == editing_status_code
            )
        return self


class VariantQuery(QueryBase):
    model = m.ProductVariant

    def apply_filters(self, filters):
        product_id = filters.get('product_id')
        if product_id:
            self.query = self.query.filter(
                m.ProductVariant.product_id == product_id
            )

        query = filters.get('query')
        if query:
            self.query = self.query.filter(or_(
                m.ProductVariant.name.like(f'%{query}%'),
                m.ProductVariant.code.like(f'%{query}%')
            ))

        editing_status_code = filters.get('editing_status_code')
        if editing_status_code:
            self.query = self.query.filter(
                m.ProductVariant.editing_status_code == editing_status_code
            )
        return self
