# coding=utf-8

from flask import g
from flask_login import login_required
from catalog.extensions import flask_restplus as fr
from catalog.validators import attribute as validators
from catalog.services.attributes import AttributeService
from catalog.validators.attribute_option import (
    CreateAttributeOptionValidator,
    UpdateAttributeOptionValidator,
    DeleteAttributeOptionValidator,
)
from catalog.api import (
    make_pagination_response,
    extract_hyper_param_from_list_request,
)
from . import schema
from catalog.utils import keep_single_spaces

attribute_ns = fr.Namespace(
    name='attributes',
    path='/attributes'
)
service = AttributeService.get_instance()  # type: AttributeService


@attribute_ns.route('', methods=['GET', 'POST'])
class Attributes(fr.Resource):
    @attribute_ns.expect(schema.AttributeListParam, location='args')
    @attribute_ns.marshal_with(schema.AttributeListResponse)
    def get(self):
        page = g.args.pop('page')
        page_size = g.args.pop('page_size')
        records, total_records = service.get_attribute_list(
            filters=g.args,
            page=page,
            page_size=page_size,
            return_full=True
        )
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'attributes': records
        }

    @attribute_ns.expect(schema.AttributeCreateData, location='body')
    @attribute_ns.marshal_with(schema.Attribute)
    def post(self):
        data = g.body
        validators.CreateAttributeValidator.validate(data)
        return service.create_attribute(data)


@attribute_ns.route('/<int:attribute_id>', methods=['GET', 'PATCH'])
class Attribute(fr.Resource):
    @attribute_ns.marshal_with(schema.Attribute)
    def get(self, attribute_id):
        return service.get_attribute(attribute_id)

    @attribute_ns.expect(schema.AttributeUpdateData, location='body')
    @attribute_ns.marshal_with(schema.Attribute)
    def patch(self, attribute_id):
        data = g.body
        validators.UpdateAttributeValidator.validate(data, attribute_id)
        attribute = service.update_attribute(attribute_id, data)
        return attribute


@attribute_ns.route('/<int:attribute_id>/options', methods=['GET', 'POST'])
class AttributeOptions(fr.Resource):
    @attribute_ns.expect(schema.AttributeOptionGetListQuery, location='args')
    @attribute_ns.marshal_with(schema.AttributeOptionGetListResponse)
    @login_required
    def get(self, attribute_id):
        filters = g.args
        page = filters.pop('page', 1)
        page_size = filters.pop('page_size', 10)

        return service.get_list_attribute_options(
            attribute_id, filters, page, page_size,
        )

    @attribute_ns.expect(schema.AttributeOptionCreateRequest, location='body')
    @attribute_ns.marshal_with(schema.AttributeOption)
    @login_required
    def post(self, attribute_id):
        data = g.body
        data['value'] = keep_single_spaces(data['value'])

        validator = CreateAttributeOptionValidator(attribute_id)
        validator.validate(data)

        return service.create_attribute_option(attribute_id, data), \
               'Tạo mới tuỳ chọn thành công'


@attribute_ns.route('/<int:attribute_id>/options/<int:option_id>', methods=['PATCH', 'DELETE'])
class AttributeOption(fr.Resource):
    @attribute_ns.expect(schema.AttributeOptionUpdateRequest, location='body')
    @attribute_ns.marshal_with(schema.AttributeOption)
    @login_required
    def patch(self, attribute_id, option_id):
        data = g.body
        data['value'] = keep_single_spaces(data['value'])

        validator = UpdateAttributeOptionValidator(attribute_id, option_id)
        validator.validate(data)
        service.update_attribute_option(option_id, data)
        return {}, 'Cập nhật tuỳ chọn thành công'

    @attribute_ns.marshal_with(schema.Attribute)
    @login_required
    def delete(self, attribute_id, option_id):
        DeleteAttributeOptionValidator(attribute_id, option_id)
        service.delete_attribute_option(option_id)
        return {}, 'Xóa thuộc tính thành công'


@attribute_ns.route('/options', methods=['GET'])
class AttributeOptionList(fr.Resource):
    @attribute_ns.expect(schema.GetOptionsOfAttributeRequestParam, location='args')
    @attribute_ns.marshal_with(schema.GetOptionsOfAttribute, many=True)
    def get(self):
        ids = g.args.get('ids')
        return service.get_options_of_attrs(ids)
