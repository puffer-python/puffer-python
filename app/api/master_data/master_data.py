# coding=utf-8
import logging

from flask import g

from catalog.api.master_data.schema import IdOnlySchema
from catalog.extensions import flask_restplus as fr
from catalog.services import seller_terminal as seller_terminal_service
from catalog.services import terminal as terminal_service
from catalog.services import terminal_group as terminal_group_service
from catalog.services import seller as seller_service
from catalog.services.products import sellable as sellable_service
from catalog.validators import master_data as master_data_validators

__author__ = 'Nam.VH'
__logger__ = logging.getLogger(__name__)

from . import schema

master_data_ns = fr.Namespace(
    'master_data',
    path='/master-data',
    description='Master Data'
)


@master_data_ns.route('/terminals', methods=['POST'])
class Terminal(fr.Resource):
    @master_data_ns.expect(schema_cls=schema.TerminalRequestSchema, location='body')
    @master_data_ns.marshal_with(schema_cls=schema.TerminalSchema)
    def post(self):
        """
        Create or update Terminal
        :return: None
        """
        terminal_schema = schema.TerminalRequestSchema()
        data = terminal_schema.load(terminal_schema.dump(g.body))
        terminal, message = terminal_service.create_or_update_terminal(data)

        return terminal, message


@master_data_ns.route('/terminal_groups', methods=['POST'])
class TerminalGroup(fr.Resource):
    @master_data_ns.expect(schema.TerminalGroupSchema, location='body')
    @master_data_ns.marshal_with(schema.TerminalGroupSchema)
    def post(self):
        group, message = terminal_group_service.create_or_update_terminal_group(g.body)
        return group, message


@master_data_ns.route('/seller_terminal_groups', methods=['POST', 'DELETE'])
class SellerTerminalGroup(fr.Resource):
    @master_data_ns.expect(schema.SellerTerminalGroupSchema, location='body')
    @master_data_ns.marshal_with(schema.SellerTerminalGroupSchema)
    def post(self):
        mapping, message = terminal_group_service.create_or_update_seller_terminal_group(g.body)
        return mapping, message

    @master_data_ns.expect(schema.SellerTerminalGroupSchema, location='body')
    @master_data_ns.marshal_with(schema.SellerTerminalGroupSchema)
    def delete(self):
        message = terminal_group_service.delete_seller_terminal_group(g.body)
        return g.body, message


@master_data_ns.route('/terminal_group_mapping', methods=['POST'])
class TerminalGroupMapping(fr.Resource):
    @master_data_ns.expect(schema.TerminalGroupMappingRequestSchema, location='body')
    @master_data_ns.marshal_with(schema.TerminalGroupMappingRequestSchema)
    def post(self):
        _, message = terminal_group_service.mapping_terminal_group(g.body)
        return g.body, message

    @master_data_ns.expect(schema.SellerTerminalGroupSchema, location='body')
    @master_data_ns.marshal_with(schema.SellerTerminalGroupSchema)
    def delete(self):
        terminal_group_service.delete_seller_terminal_group(g.body)
        return {}, 'Delete success'


@master_data_ns.route('/sellers', methods=['POST'])
class Seller(fr.Resource):
    @master_data_ns.expect(schema_cls=schema.SellerRequestSchema, location='body')
    @master_data_ns.marshal_with(schema_cls=schema.IdOnlySchema)
    def post(self):
        """
        Create or update Terminal
        :return: None
        """
        seller_schema = schema.SellerRequestSchema()
        data = seller_schema.load(seller_schema.dump(g.body))
        seller_id, message = seller_service.create_or_update(data)

        response = IdOnlySchema()
        response.id = seller_id

        return response, message


@master_data_ns.route('/sellers-terminals', methods=['POST', 'DELETE'])
class SellerTerminal(fr.Resource):
    @master_data_ns.expect(schema_cls=schema.SellerTerminalRequestSchema, location='body')
    @master_data_ns.marshal_with(schema_cls=schema.SellerTerminalSchema)
    def post(self):
        """
        Create or update Terminal
        :return: None
        """
        seller_terminal_schema = schema.SellerTerminalRequestSchema()
        data = seller_terminal_schema.load(seller_terminal_schema.dump(g.body))
        seller_terminal, message = seller_terminal_service.create_or_update_seller_terminal(data)

        return seller_terminal, message

    @master_data_ns.expect(schema_cls=schema.SellerTerminalRequestSchema, location='body')
    @master_data_ns.marshal_with(schema_cls=schema.IdOnlySchema)
    def delete(self):
        """
        Create or update Terminal
        :return: None
        """
        seller_terminal_id = seller_terminal_service.delete_seller_terminal(g.body)

        response = IdOnlySchema()
        response.id = seller_terminal_id

        return response, 'Xóa seller terminal thành công'


@master_data_ns.route('/sellable_products/srm_status/<int:sellable_id>', methods=['PATCH'])
class UpdateSrmStatus(fr.Resource):
    @master_data_ns.expect(schema.UpdateSrmStatus, location='body')
    @master_data_ns.marshal_with(schema.UpdateStatusSrmResponse)
    def patch(self, sellable_id):
        master_data_validators.UpdateSrmStatusValidator.validate({
            'sellable_id': sellable_id,
            'code': g.body['code']
        })
        sellable = sellable_service.update_status_from_srm(sellable_id, g.body['code'])
        return sellable, 'Cập nhật trạng thái thành công'


@master_data_ns.route('/selling-seller-platform', methods=['POST'])
class SellingSellerPlatform(fr.Resource):
    @master_data_ns.expect(schema.SellingSellerPlatform, location='body')
    @master_data_ns.marshal_with(schema.Schema)
    def post(self):
        data = g.body
        seller_service.assign_new_selling_platform(data.get('seller_id'), data.get('platform_id'),
                                                   data.get('owner_seller_id'),
                                                   data.get('is_default'))
        return {}, 'Thành công'
