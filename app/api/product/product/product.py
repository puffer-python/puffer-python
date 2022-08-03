# coding=utf-8

import flask
from flask_login import (
    login_required,
    current_user,
)

from flask import g
from catalog.extensions import flask_restplus as fr
from catalog.services.products.product import ProductService, get_psd_product
from catalog.validators import products as validators
from . import schema

product_ns = fr.Namespace(
    name='product',
    path='/products'
)

service = ProductService.get_instance()
@product_ns.route('', methods=['POST', 'GET'])
class Products(fr.Resource):
    @product_ns.expect(schema.ProductCreateRequestBody, location='body')
    @product_ns.marshal_with(schema.ProductCreateResponse)
    @login_required
    def post(self):
        data = flask.g.body
        validators.ProductCommonValidator.validate(data)
        product = service.create_product(data, current_user.email)
        return product, "Tạo mới sản phẩm thành công"

    @product_ns.expect(schema.ProductGetRequestParams, location='args')
    @product_ns.marshal_with(schema.ProductGetListResponse)
    @login_required
    def get(self):
        filters = g.args
        page_size = filters.pop('page_size')
        page = filters.pop('page')
        products, total_records = service.get_product_list(filters=filters, page_size=page_size, page=page, sort_field='id', sort_order='ascend')
        return {
            "current_page": page,
            "page_size": page_size,
            "total_records": total_records,
            "products": products
        }
        
@product_ns.route('/draft', methods=['GET', 'DELETE'])
class DraftProduct(fr.Resource):
    @product_ns.marshal_with(schema.GenericProduct)
    @login_required
    def get(self):
        return service.get_draft_product()

    @product_ns.marshal_with(schema.GenericProduct)
    @login_required
    def delete(self):
        validators.DeleteDraftProductValidator.validate({'email': current_user.email})
        product = service.delete_draft_product(current_user.email)
        return {'id': product.id}, 'Xóa sản phẩm nháp thành công'


@product_ns.route('/<int:product_id>', methods=['GET', 'PATCH'])
class Product(fr.Resource):
    @product_ns.marshal_with(schema.GenericProduct)
    @login_required
    def get(self, product_id):
        validators.GetProductInfoValidator.validate({'product_id': product_id})
        return service.get_product(product_id)

    @product_ns.expect(schema.ProductUpdateRequestBody, location='body')
    @product_ns.marshal_with(schema.ProductCreateResponse)
    @login_required
    def patch(self, product_id):
        data = flask.g.body
        validators.ProductUpdateValidator.validate(
            {'data': data},
            obj_id=product_id
        )

        product = service.update_product(data, product_id)

        return product, "Cập nhật sản phẩm thành công"


@product_ns.route('/history/<int:sellable_id>', methods=['GET'])
class ProductHistory(fr.Resource):
    @product_ns.marshal_with(schema.ProductHistory, as_list=True)
    @login_required
    def get(self, sellable_id):
        return service.get_product_history(sellable_id=sellable_id)


@product_ns.route('/psd', methods=['GET'])
class ProductPsd(fr.Resource):
    def get(self):
        return get_psd_product()
