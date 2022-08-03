# coding=utf-8
import logging
import os
import flask_restplus as fr

from catalog.api import api
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class MediaUrlField(fr.fields.String):
    def format(self, value):
        if not value:
            return os.getenv('NO_IMAGE_URL')
        return value


class ChannelField(fr.fields.Raw):
    def format(self, value):
        cid = getattr(value, 'channel_id')

        return m.SaleChannel.query.get(cid).name


class SaleCategoryField(fr.fields.Raw):
    def format(self, value):
        return value.name if value else None


class ProductTypeField(fr.fields.String):
    def format(self, value):
        ptype = m.Misc.query.filter(
            m.Misc.type == 'product_type',
            m.Misc.code == value
        ).first()

        return ptype.name if ptype else None


class UnitPOField(fr.fields.Integer):
    def format(self, value):
        unit = m.Unit.query.filter(m.Unit.id == value.unit_po_id).first()

        return unit.name if unit else None


file = api.model('Attachment', {
    'id': fr.fields.Integer(required=True, description='Identifier'),
    'url': MediaUrlField(required=True, description='File url'),
    'name': fr.fields.String(required=True, description='File name')
})

image = api.model('Image', {
    'id': fr.fields.Integer(required=True, description='Identifier'),
    'url': MediaUrlField(required=True, description='Image url'),
    'label': fr.fields.String(required=True, description='Image name'),
    'is_displayed': fr.fields.Boolean(required=True, default=False,
                                      description='Can be displayed?'),
    'priority': fr.fields.Integer(required=True, description='Image priority'),
    'status': fr.fields.Integer(required=False, description='Image status')
})

common_schema = api.model('ProductCommonDataLog', {
    'id': fr.fields.Integer(),
    'sku': fr.fields.String(),
    'name': fr.fields.String(),
    'attribute_set': fr.fields.String(description='Attribute set name',
                                      attribute='attribute_set_name'),
    'selling_status': fr.fields.String(attribute='selling_status',
                                       description='Selling status'),
    
})
