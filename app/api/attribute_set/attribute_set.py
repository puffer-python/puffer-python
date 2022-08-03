# coding=utf-8
import logging

from flask import g

from catalog.extensions import flask_restplus as fr
from catalog.services.attribute_sets import (
    AttributeSetConfigService,
    AttributeSetService
)
from catalog.validators import attribute_set as validators
from . import schema

__author__ = 'Kien.HT'

from catalog.extensions.request_logging import log_request

_logger = logging.getLogger(__name__)

attribute_set_ns = fr.Namespace(
    name='Attribute set',
    path='/attribute_sets',
    description='Attribute set operations'
)

service = AttributeSetService.get_instance()

attr_set_service = AttributeSetService.get_instance()
config_service = AttributeSetConfigService.get_instance()


@attribute_set_ns.route('/<int:set_id>', methods=['GET', 'PATCH'])
class AttributeSet(fr.Resource):
    @attribute_set_ns.marshal_with(schema.AttributeSetDetail)
    def get(self, set_id):
        """
        API lấy thông tin các groups và attributes của attribute set
        :param int set_id:
        :return:
        """
        res = attr_set_service.get_attribute_set_content(set_id)

        return res

    @log_request
    @attribute_set_ns.expect(schema.UpdateAttributeSetRequestBody, location='body')
    @attribute_set_ns.marshal_with(schema.UpdateAttributeSetResponse)
    def patch(self, set_id):
        data = g.body
        validators.UpdateAttributeSetValidator.validate({
            'set_id': set_id,
            'data': data
        })
        return attr_set_service.update_attribute_set(set_id, data['attribute_groups'])


@attribute_set_ns.route('', methods=['GET', 'POST'])
class AttributeSetList(fr.Resource):
    @attribute_set_ns.expect(schema.GetAttributeSetListParam, location='args')
    @attribute_set_ns.marshal_with(schema.GetAttributeSetListResponse)
    def get(self):
        """
        API cho phép lấy danh sách attribute set
        :return:
        """
        page = g.args.pop('page')
        page_size = g.args.pop('page_size')
        sort_field = g.args.pop('sort_field')
        sort_order = g.args.pop('sort_order')
        attribute_sets, total_records = attr_set_service.get_attribute_set_list(
            g.args, sort_field, sort_order, page, page_size)
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'attribute_sets': attribute_sets
        }

    @attribute_set_ns.expect(schema.CreateAttributeSetRequestBody, location='body')
    @attribute_set_ns.marshal_with(schema.CreateAttributeSetResponse)
    def post(self):
        data = g.body
        validators.AttributeSetCreateValidator.validate(data)
        attribute_set = attr_set_service.create_attribute_set(data)
        return attribute_set


@attribute_set_ns.route('/<int:set_id>/configs', methods=['GET', 'PUT'])
class AttributeSetConfigs(fr.Resource):
    @attribute_set_ns.marshal_with(schema.AttributeSetConfigList)
    def get(self, set_id):
        result = config_service.get_config_list(set_id)
        return result

    @attribute_set_ns.expect(schema.UpdateConfigsAttributeSetRequestBody, location='body')
    @attribute_set_ns.marshal_with(schema.UpdateConfigsAttributeSetResponse)
    def put(self, set_id):
        data = {
            'attribute_set_id': set_id,
            **g.body
        }
        res = config_service.create_config(data)
        return res


@attribute_set_ns.route('/configs/<int:config_id>', methods=['GET'])
class AttributeSetConfig(fr.Resource):
    @attribute_set_ns.marshal_with(schema.GetCommonAttributeSetConfigResponse)
    def get(self, config_id):
        return config_service.get_config_detail_common(config_id)


@attribute_set_ns.route('/configs/<int:config_id>/detail', methods=['GET', 'PUT'])
class AttributeSetConfigDetail(fr.Resource):
    @attribute_set_ns.expect(schema.GetDetailAttributeSetConfigParams, location='args')
    @attribute_set_ns.marshal_with(schema.GetDetailAttributeSetConfigResponse)
    def get(self, config_id):
        return config_service.get_config_detail(config_id, g.args['field_display'])

    @attribute_set_ns.expect(schema.UpdateConfigAttributeSetRequestBody, many=True, location='body')
    @attribute_set_ns.marshal_with(schema.UpdateConfigAttributeSetResponse)
    def put(self, config_id):
        data = g.body
        detail_config = config_service.update_attribute_set_config(config_id, data)
        return {
            'attribute_set_configs': detail_config
        }


@attribute_set_ns.route('/<int:set_id>/variation_attributes', methods=['PATCH', 'POST'])
class VariationAttribute(fr.Resource):
    @attribute_set_ns.expect(schema.UpdateOrderVariationAttributeRequestBody, location='body')
    @attribute_set_ns.marshal_with(schema.UpdateOrderVariationAttributeResponse)
    def patch(self, set_id):
        data = g.body
        validators.UpdateOrderVariationAttributeValidator.validate({
            'set_id': set_id,
            'ids': data.get('ids')
        })
        return {
            'variation_attributes': attr_set_service.update_order_variation_attribute(set_id, data.get('ids'))
        }

    @attribute_set_ns.expect(schema.CreateVariationAttributeRequestBody, location='body')
    @attribute_set_ns.marshal_with(schema.VariationAttribute)
    def post(self, set_id):
        data = g.body
        validators.CreateVariationAttributeValidator.validate({
            'set_id': set_id,
            **data
        })
        return attr_set_service.create_attribute_variation(set_id, **data)
