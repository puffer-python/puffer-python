#coding=utf-8

from catalog.extensions import flask_restplus as fr
from catalog.services.tax import TaxService
from . import schema


tax_ns = fr.Namespace(
    name='tax',
    path='/taxes'
)
service = TaxService.get_instance()

@tax_ns.route('', methods=['GET'])
class Tax(fr.Resource):
    @tax_ns.marshal_with(schema.Tax, many=True)
    def get(self):
        return service.get_taxes_list()
