# coding=utf-8

from flask import g
from flask_login import (
    login_required,
    current_user,
)

from catalog.extensions import flask_restplus as fr
from catalog.services.categories import CategoryService
from catalog.services.master_categories import MasterCategoryService
from catalog.validators.category import (
    GetCategoryTreeValidator,
    CreateCategoryValidator,
    UpdateCategoryValidator,
    CloneMasterCategory
)
from . import schema
from catalog.api.master_category import schema as master_category_schema

import catalog.services.categories.category as category_service
import catalog.services.seller as seller_service
from catalog.extensions.request_logging import log_request

category_ns = fr.Namespace(
    name='category',
    path='/categories'
)

service = CategoryService.get_instance()
master_category_service = MasterCategoryService.get_instance()


@category_ns.route('', methods=['GET', 'POST'])
class Category(fr.Resource):
    @log_request
    @category_ns.expect(schema.ListCategoriesParam, location='args')
    @category_ns.marshal_with(schema.ListCategoriesResponse)
    def get(self):
        page = g.args.pop('page')
        page_size = g.args.pop('page_size')
        g.args['depth'] = g.args.pop('level')
        platform_id = g.args.get('platform_id')
        if platform_id:
            seller_id = seller_service.get_platform_owner(platform_id)
        else:
            seller_id = seller_service.get_default_platform_owner_of_seller(current_user.seller_id)
        seller_id = seller_id or current_user.seller_id
        categories, total_records = service.get_list_categories(
            g.args, page, page_size, seller_id=seller_id
        )
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'categories': categories
        }

    @category_ns.expect(schema.CategoryPostSchema, location='body')
    @category_ns.marshal_with(schema.CategoryGeneric)
    @login_required
    def post(self):
        data = CreateCategoryValidator.validate(g.body)
        return service.create_category(data=data)


@category_ns.route('/<int:category_id>', methods=['GET', 'PATCH'])
class CategoryDetail(fr.Resource):
    @category_ns.marshal_with(schema.CategoryDetail)
    def get(self, category_id):
        return service.get_category_with_id(category_id)

    @log_request
    @category_ns.expect(schema.CategoryUpdateSchema, location='body')
    @category_ns.marshal_with(schema.CategoryGeneric)
    @login_required
    def patch(self, category_id):
        data = UpdateCategoryValidator.validate(g.body, obj_id=category_id)
        return service.update_category(data=data, obj_id=category_id)


@category_ns.route('/<int:category_id>/children', methods=['GET'])
class CategoryTree(fr.Resource):
    @category_ns.marshal_with(schema.CategoryTreeSchema)
    def get(self, category_id):
        GetCategoryTreeValidator.validate({'category_id': category_id})
        return service.get_category_tree(category_id)


@category_ns.route('/recommendation', methods=['GET'])
class CategoryRecommendation(fr.Resource):
    @log_request
    @category_ns.expect(schema.CategoryRecommendationRequest, location='args')
    @category_ns.marshal_with(master_category_schema.CategoryRecommendationResponse, many=True)
    @login_required
    def get(self):
        return master_category_service.get_recommendation_category(**g.args)


@category_ns.route('/clone_from_master_categories', methods=['POST'])
class CategoryClone(fr.Resource):
    @category_ns.expect(schema.CategoryCloneMasterCategorySchema, location='body', allow_none=False)
    @category_ns.marshal_with(schema.Schema)
    @login_required
    def post(self):
        CloneMasterCategory.validate(g.body)
        service.clone_from_master_category(**g.body)
        return {}, "Nhận yêu cầu thành công"


@category_ns.route('/<int:category_id>/shipping_type/sku', methods=['PATCH'])
class CategoryAppliedShippingTypeToSku(fr.Resource):
    @category_ns.marshal_with(schema.Schema)
    @login_required
    def patch(self, category_id):
        category_service.apply_shipping_type_to_skus(category_id)
        return None, "Gán loại hình vận chuyển thành công"


@category_ns.route('/bulk/<int:seller_id>', methods=['POST'])
class InsertBulkCategories(fr.Resource):
    @category_ns.expect(schema.CategoryPostBulkSchema, location='body')
    @category_ns.marshal_with(schema.Schema)
    @login_required
    def post(self, seller_id):
        from catalog.services.categories.category_bulk import create_bulk_categories
        data = CreateCategoryValidator.validate(g.body)
        create_bulk_categories(data, seller_id)
        return {}, "Thêm danh mục thành công"


@category_ns.route('/import/<int:seller_id>', methods=['POST'])
class ImportCategories(fr.Resource):
    @category_ns.marshal_with(schema.Schema)
    @login_required
    def post(self, seller_id):
        import numpy as np
        import pandas as pd
        from flask import request
        from catalog.services.categories.category_bulk import create_bulk_categories

        def get_cell_value(r, idx):
            if len(r) >= idx + 1:
                val = r[idx]
                if val is np.NAN:
                    return ''
                return val
            return ''

        files = request.files
        r = files.get('file')
        df = pd.io.excel.read_excel(r.stream, header=4, dtype=str)
        categories = []
        for _, (r) in df.iterrows():
            if len(r) < 2:
                continue
            categories.append({
                'code1': get_cell_value(r, 0),
                'name1': get_cell_value(r, 1),
                'eng_name1': get_cell_value(r, 2),
                'code2': get_cell_value(r, 3),
                'name2': get_cell_value(r, 4),
                'eng_name2': get_cell_value(r, 5),
                'code3': get_cell_value(r, 6),
                'name3': get_cell_value(r, 7),
                'eng_name3': get_cell_value(r, 8),
            })
        create_bulk_categories({'categories': categories}, seller_id)
        return {}, "Import danh mục thành công"
