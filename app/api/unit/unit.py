# coding=utf-8
import logging

from flask import g

from catalog.extensions import flask_restplus as fr
from catalog.services import unit as svr
from . import schema

__author__ = 'Kien.HT'

from ...validators.units import CreateUnitsValidator, UpdateUnitsValidator, DeleteUnitsValidator

_logger = logging.getLogger(__name__)

unit_ns = fr.Namespace(
    'unit',
    path='/units',
    description='Unit set operations'
)


@unit_ns.route('', methods=['POST', 'GET'])
class Units(fr.Resource):
    @unit_ns.expect(schema.UnitRequest, location='body')
    @unit_ns.marshal_with(schema_cls=schema.UnitSchema)
    def post(self):
        CreateUnitsValidator.validate(g.body)
        unit = svr.create_unit(g.body)

        return unit, "Tạo mới đơn vị tính thành công"

    @unit_ns.expect(schema.UnitGetListRequest, location='args')
    @unit_ns.marshal_with(schema.UnitGetListResponse)
    def get(self):
        units, total_records = svr.get_list_units(**g.args)

        return {
            'current_page': g.args['page'],
            'page_size': g.args['page_size'],
            'total_records': total_records,
            'units': units
        }


@unit_ns.route('/<int:unit_id>', methods=['PATCH', 'DELETE'])
class Unit(fr.Resource):
    @unit_ns.expect(schema_cls=schema.UnitUpdateRequest, location='body')
    @unit_ns.marshal_with(schema_cls=schema.UnitSchema)
    def patch(self, unit_id):
        UpdateUnitsValidator.validate(g.body, obj_id=unit_id)
        unit = svr.update_unit(unit_id, g.body)

        return unit, "Cập nhật đơn vị tính thành công"

    @unit_ns.marshal_with(schema_cls=schema.Schema)
    def delete(self, unit_id):
        DeleteUnitsValidator.validate(data={}, obj_id=unit_id)
        svr.delete_unit(unit_id)

        return {}, "Xóa đơn vị tính thành công"