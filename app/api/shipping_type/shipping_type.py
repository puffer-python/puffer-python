# coding=utf-8

from flask import g
from flask_login import login_required

from catalog.extensions import flask_restplus as fr
from . import schema

import catalog.services.shipping_types.shipping_type as service

shipping_type_ns = fr.Namespace(
    'shipping_type',
    path='/shipping_types',
)


@shipping_type_ns.route('', methods=['GET', 'POST'])
@shipping_type_ns.route("/<int:r_id>", methods=["PATCH"])
class ShippingTypes(fr.Resource):
    @shipping_type_ns.expect(schema_cls=schema.ShippingTypeListParams, location='args')
    @shipping_type_ns.marshal_with(schema_cls=schema.ShippingTypeListResponse)
    def get(self):
        """
        Get list shipping type, order by Id desc
        Allow parameter:
            name: filter by name
            code: filter by code
            query: filter by name or code
        """
        page = g.args['page']
        page_size = g.args['page_size']
        shipping_types, total_records = service.get_shipping_type_list(
            filters=g.args,
            sort_order='descend',
            sort_field='is_default',
            page=page,
            page_size=page_size)
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'shipping_types': shipping_types
        }

    @shipping_type_ns.expect(schema_cls=schema.CreateShippingTypeRequest, location='body')
    @shipping_type_ns.marshal_with(schema_cls=schema.ShippingTypeSchema)
    @login_required
    def post(self):
        """
        Create shipping type
        """
        res = service.create_shipping_type(data=g.body)
        return res, "Tạo mới Loại hình vận chuyển thành công"

    @shipping_type_ns.expect(schema_cls=schema.UpdateShippingTypeRequest, location='body')
    @shipping_type_ns.marshal_with(schema_cls=schema.ShippingTypeSchema)
    @login_required
    def patch(self, r_id):
        """
        Update shipping type
        :param r_id: id of shipping type record
        """
        dto = {
            'name': g.body['name'],
            'id': r_id
        }
        res = service.update_shipping_type(dto)
        return res, "Cập nhật Loại hình vận chuyển thành công"
