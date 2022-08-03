import logging

from flask_restplus import Resource, fields
from flask_restplus.reqparse import RequestParser
from flask_restplus import Namespace

from catalog.models import attribute_option, AttributeOption, Attribute

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)

api = Namespace('attributes', path='/attribute_options',
                description='Attribute Option API')

request_parser = RequestParser(bundle_errors=True)

request_parser.add_argument('attribute_ids', required=True, type=str)

detail = api.model('AttributeOptionDetail', {
    'id': fields.Integer(),
    'value': fields.String(),
    'unit_id': fields.Integer(),
    'unit_code': fields.String()
})

response_api = api.model('AttributeOptions', {
    'attribute_id': fields.Integer(),
    'options': fields.List(fields.Nested(detail)),
})


@api.route('', methods=['GET', 'POST'])
class AttributesOptionAPI(Resource):
    @api.expect(request_parser, validate=True)
    @api.marshal_list_with(response_api)
    def get(self):
        result = []

        attribute_ids = request_parser.parse_args().get('attribute_ids')

        for attribute_id in attribute_ids.split(','):
            options = AttributeOption.query.filter(
                AttributeOption.attribute_id == attribute_id
            ).all()

            result.append({
                'attribute_id': attribute_id,
                'options': options
            })

        return result
