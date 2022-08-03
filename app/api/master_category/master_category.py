# coding=utf-8
from flask import g

from catalog.extensions import flask_restplus as fr
from catalog.validators.master_category import (
    CreateMasterCategoryValidator,
    UpdateMasterCategoryValidator,
    GetMasterCategoryValidator,
    GetMasterCategoryTreeValidator,
)
from catalog.services.master_categories import MasterCategoryService
from . import schema


service = MasterCategoryService.get_instance()

master_category_ns = fr.Namespace(
    'master_category',
    path='/master_categories',
    description='Master category operations'
)


@master_category_ns.route('', methods=['GET', 'POST'])
class MasterCategories(fr.Resource):
    @master_category_ns.expect(schema_cls=schema.MasterCategoryListParams, location='args')
    @master_category_ns.marshal_with(schema_cls=schema.MasterCategoryListResponse)
    def get(self):
        page = g.args['page']
        page_size = g.args['page_size']
        master_categories, total_records = service.get_master_category_list(
            g.args, page, page_size)
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'master_categories': master_categories
        }

    @master_category_ns.expect(schema_cls=schema.CreateMasterCategoryRequestBody, location='body')
    @master_category_ns.marshal_with(schema_cls=schema.MasterCategorySchema)
    def post(self):
        """
        Create new category
        :return: None
        """
        data = CreateMasterCategoryValidator.validate(g.body)
        category = service.create_master_category(data=data)

        return category, "Thêm mới danh mục thành công"


@master_category_ns.route('/<int:cat_id>', methods=['PATCH', 'GET'])
class MasterCategory(fr.Resource):
    @master_category_ns.expect(schema_cls=schema.UpdateMasterCategoryRequest, location='body')
    @master_category_ns.marshal_with(schema_cls=schema.MasterCategorySchema)
    def patch(self, cat_id):
        UpdateMasterCategoryValidator.validate({
            'cat_id': cat_id,
            **g.body
        })
        return service.update_master_category(cat_id, g.body)

    @master_category_ns.marshal_with(schema_cls=schema.MasterCategorySchema)
    def get(self, cat_id):
        GetMasterCategoryValidator.validate({'cat_id': cat_id})
        return service.get_master_category(cat_id)


@master_category_ns.route('/<int:sc_id>/children', methods=['GET'])
class MasterCategoryTree(fr.Resource):
    @master_category_ns.marshal_with(schema_cls=schema.MasterCategoryTreeSchema)
    def get(self, sc_id):
        GetMasterCategoryTreeValidator.validate({
            'master_category_id': sc_id
        })
        return service.get_master_category_tree(sc_id)
