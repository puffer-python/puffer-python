# coding=utf-8
from flask import g

from catalog.extensions import flask_restplus as fr
from catalog.validators.sale_category import (
    CreateSaleCategoryValidator,
    UpdatePositionValidator,
    UpdateSaleCategoryValidator
)
from catalog.services.sale_categories import SaleCategoryService
from . import schema


service = SaleCategoryService.get_instance()

sale_category_ns = fr.Namespace(
    'sale_category',
    path='/sale_categories',
)


@sale_category_ns.route('', methods=['GET', 'POST'])
@sale_category_ns.route("/<int:id_node>/position", methods=["PATCH"])
class MasterCategories(fr.Resource):
    @sale_category_ns.expect(schema_cls=schema.SaleCategoryListParams, location='args')
    @sale_category_ns.marshal_with(schema_cls=schema.SaleCategoryListResponse)
    def get(self):
        page = g.args['page']
        page_size = g.args['page_size']
        sale_categories, total_records = service.get_sale_category_list(
            g.args, page, page_size)
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'sale_categories': sale_categories
        }

    @sale_category_ns.expect(schema_cls=schema.SaleCategoryRequest, location='body')
    @sale_category_ns.marshal_with(schema_cls=schema.SaleCategorySchema)
    def post(self):
        """
        Create new category
        :return: None
        """
        data = CreateSaleCategoryValidator.validate(g.body)
        sc = service.create_sale_category(data=data)

        return sc, "Thêm mới danh mục thành công"

    @sale_category_ns.expect(schema_cls=schema.UpdatePositionRequest, location='body')
    def patch(self, id_node):
        """
        Update position for sale category
        :param id_node:
        """
        g.body.update({'id_node': id_node})
        data = UpdatePositionValidator.validate(g.body)
        service.update_position(**data)

        return {
            "code": "SUCCESS",
            "message": "Cập nhật vị trí danh mục thành công"
        }


@sale_category_ns.route('/<int:sc_id>', methods=['PATCH'])
class SaleCategory(fr.Resource):
    @sale_category_ns.expect(schema_cls=schema.UpdateSaleCategoryRequest, location='body')
    @sale_category_ns.marshal_with(schema_cls=schema.SaleCategorySchema)
    def patch(self, sc_id):
        """
        Edit sale category
        :param sc_id:
        :return:
        """
        g.body.update({'sc_id': sc_id})
        data = UpdateSaleCategoryValidator.validate(g.body)

        return service.update_sale_category(sc_id, data)


@sale_category_ns.route('/<int:sc_id>/children', methods=['GET'])
class SaleCategoryTree(fr.Resource):
    @sale_category_ns.marshal_with(schema_cls=schema.SaleCategoryTreeSchema)
    def get(self, sc_id):
        return service.get_sale_category_tree(sc_id)
