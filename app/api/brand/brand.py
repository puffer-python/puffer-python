# coding=utf-8
import logging
from flask import g

from catalog.extensions.flask_cache import cache
from catalog.extensions import flask_restplus as fr
from catalog.services import brand as svr
from catalog.validators.brand import (
    CreateBrandValidator,
    UpdateBrandValidator
)

from . import schema

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)

brand_ns = fr.Namespace(
    'brand',
    path='/brands',
    description='Brand set operations'
)


@brand_ns.route('', methods=['GET', 'POST'])
class Brands(fr.Resource):
    @brand_ns.expect(schema.BrandListRequest, location='args')
    @brand_ns.marshal_with(schema.BrandListSchema)
    def get(self):
        """

        :return:
        """
        data = g.args
        res = svr.get_brand_list(**data)
        return res

    @brand_ns.expect(schema.BrandRequest, location='body')
    @brand_ns.marshal_with(schema_cls=schema.BrandSchema)
    def post(self):
        data = CreateBrandValidator.validate(g.body)
        brand = svr.create_brand(data)

        return brand, "Tạo mới thương hiệu thành công"


@brand_ns.route('/<int:brand_id>', methods=['GET', 'PATCH'])
class Brand(fr.Resource):
    @brand_ns.marshal_with(schema_cls=schema.BrandSchema)
    def get(self, brand_id):
        brand = svr.get_brand(brand_id)
        return brand

    @brand_ns.expect(schema_cls=schema.BrandUpdateRequest, location='body')
    @brand_ns.marshal_with(schema_cls=schema.BrandSchema)
    def patch(self, brand_id):
        brand = svr.get_brand(brand_id)
        data = UpdateBrandValidator.validate(g.body, obj_id=brand.id)
        brand = svr.update_brand(brand.id, data)
        return brand, "Cập nhật thương hiệu thành công"


@brand_ns.route('/images', methods=['PATCH'])
class BrandImage(fr.Resource):
    @brand_ns.expect(schema_cls=schema.BrandUpdateImageRequest, location='body')
    @brand_ns.marshal_with(schema_cls=schema.BrandSchema)
    def patch(self):
        data = g.body
        payload = {
            'logo': data.get('logo')
        }
        brand = svr.update_brand_by_code(data.get('code'), payload)
        return brand, "Cập nhật ảnh thương hiệu thành công"
