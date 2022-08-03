# coding=utf-8

from flask import g
from flask_login import (
    login_required,
    current_user,
)

from catalog.extensions import flask_restplus as fr
from catalog.services.products import ProductVariantService
from catalog.validators.variant import (
    CreateVariantValidator,
    UpdateVariantValidatorWithoutCheckImage,
    CreateVariantAttributeValidator,
    GetListVariantValidator,
    GetListVariantAttributeListValidator, UpsertExternalVariantImagesValidator,
)
from . import schema

variant_ns = fr.Namespace(
    name='variant',
    path='/variants'
)
variant_service = ProductVariantService.get_instance()


@variant_ns.route('', methods=['GET', 'POST', 'PATCH'])
class Variant(fr.Resource):
    @variant_ns.expect(schema.CreateVariantsBodyRequest, location='body')
    @variant_ns.marshal_with(schema.CreateVariantsResponse)
    @login_required
    def post(self):
        data = CreateVariantValidator.format_data(g.body)
        CreateVariantValidator.validate(
            {'data': data, 'seller_id': current_user.seller_id, 'created_by': current_user.email})
        return {
            'product_id': data['product_id'],
            'variants': variant_service.create_variants(data['product_id'],
                                                        data.get('variants'),
                                                        current_user.email)
        }

    @variant_ns.expect(schema.UpdateVariantsData, location='body')
    @variant_ns.marshal_with(schema.UpdateVariantsResponse)
    @login_required
    def patch(self):
        data = g.body
        UpdateVariantValidatorWithoutCheckImage.validate({'data': data})
        return {
            'variants': variant_service.update_variant(data)
        }

    @variant_ns.expect(schema.GetVariantListParam, location='args')
    @variant_ns.marshal_with(schema.GetVariantListResponse)
    @login_required
    def get(self):
        page = g.args.pop('page')
        page_size = g.args.pop('page_size')
        sort_field = g.args.pop('sort_field')
        sort_order = g.args.pop('sort_order')
        GetListVariantValidator.validate(g.args)
        variants, total_records = variant_service.get_variants(
            g.args, page, page_size, sort_field, sort_order
        )
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'variants': variants
        }


@variant_ns.route('/attributes', methods=['POST', 'GET'])
class VariantAttribute(fr.Resource):
    @variant_ns.expect(schema.CreateVariantAttributeRequest, location='body')
    @variant_ns.marshal_with(schema.CreateVariantAttributeResponse, many=True)
    @login_required
    def post(self):
        validator = CreateVariantAttributeValidator()
        validator.validate({
            'data': g.body,
            'seller_id': current_user.seller_id
        })
        return variant_service.create_bulk_variant_attributes(g.body)

    @variant_ns.expect(schema.GetVariantAttributeListParam, location='args')
    @variant_ns.marshal_with(schema.GetVariantAttributeListResponse)
    @login_required
    def get(self):
        variant_ids = g.args['variant_ids']
        GetListVariantAttributeListValidator.validate({'variant_ids': variant_ids})
        ret = variant_service.get_variant_attribute_list(variant_ids)
        return {
            'variants': ret
        }


@variant_ns.route('/<int:variant_id>/external_images', methods=['PATCH'])
class VariantImage(fr.Resource):
    @variant_ns.expect(schema.CreateExternalImageParams, location='body')
    @variant_ns.marshal_with(schema.CreateExternalImageResponse)
    @login_required
    def patch(self, variant_id):
        data = {
            'id': variant_id,
            **g.body
        }
        UpsertExternalVariantImagesValidator.validate({'data': {'variants': [data]}})

        return {
            'request_id': variant_service.create_variant_images_from_external_url(data)
        }, "Nhận dữ liệu thành công, hệ thống đang tạo mới ảnh cho biến thể"
