# coding=utf-8
import logging

from catalog.extensions import flask_restplus as fr
from . import schema

__author__ = 'Dung.BV'

from ...services.attribute_sets.attribute_set import get_manufacture_attribute

_logger = logging.getLogger(__name__)

manufacture_ns = fr.Namespace(
    'manufacture',
    path='/manufactures',
    description='The manufacture APIs'
)


@manufacture_ns.route('', methods=['GET'])
class Manufacture(fr.Resource):
    @manufacture_ns.marshal_list_with(schema.ManufactureResponse)
    def get(self):
        """

        :return:
        """
        return get_manufacture_attribute()
