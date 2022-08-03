# coding=utf-8
import logging
from flask_login import current_user

from catalog import models as m
from catalog.services import Singleton
from catalog.extensions import exceptions as exc
from catalog.services.categories import category

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class ExtraService(Singleton):
    def get_extra_info(self, args):
        map_queries = {
            'editing_status': m.EditingStatus.query,
            'units': m.Unit.query,
            'product_types': m.Misc.query.filter(m.Misc.type == 'product_type'),
            'taxes': m.Tax.query,
            'manage_stock_types': m.Misc.query.filter(
                m.Misc.type == 'manage_stock_type'
            ),
            'selling_status': m.SellingStatus.query,
            'warranty_types': m.Misc.query.filter(
                m.Misc.type == 'warranty_type'
            ),
            'import_types': m.Misc.query.filter(
                m.Misc.type == 'import_type'
            ),
            'import_status': m.Misc.query.filter(
                m.Misc.type == 'import_status'
            ),
            'on_off_status': m.Misc.query.filter(
                m.Misc.type == 'on_off_status'
            ),
            'shipping_types': m.Misc.query.filter(
                m.Misc.type == 'shipping_type'
            ),
            'sellers': m.Seller.query,
            'colors': m.Color.query,
            'product_units': m.ProductUnit.query,
            'seo_configs': m.Misc.query.filter(
                m.Misc.type == 'seo_config'
            ).order_by(m.Misc.position),
        }
        req_type = args.get('types')
        if req_type:
            return {k: v.all() for k, v in map_queries.items() if k in req_type.split(',')}
        return {k: v.all() for k, v in map_queries.items()}

    def get_old_extra_data(self, args, seller_id):
        _map_queries = {
            'brands': m.Brand.query.filter(
                m.Brand.is_active == 1
            ),
            'attribute_sets': m.AttributeSet.query,
            'categories': category.get_leaf_tree(
                seller_id=seller_id
            ),
            'selling_status': m.SellingStatus.query,
            'editing_status': m.EditingStatus.query,
            'warranty_types': m.Misc.query.filter(m.Misc.type == 'warranty_type'),
            'objectives': m.Misc.query.filter(m.Misc.type == 'objective'),
            'product_types': m.Misc.query.filter(m.Misc.type == 'product_type'),
            'colors': m.Color.query,
            'units': m.Unit.query,
            'product_units': m.ProductUnit.query,
            'product_lines': m.Category.query.filter(
                m.Category.depth == 1
            ),
            'sale_categories': m.SaleCategory.query,
            'seo_configs': m.Misc.query.filter(
                m.Misc.type == 'seo_config'
            ).order_by(m.Misc.position),
            'seo_object_types': m.Misc.query.filter(
                m.Misc.type == 'seo_object_type'
            ),
            'sellers': m.Seller.query,
            'reason_types': m.Misc.query.filter(m.Misc.type == 'reason_type'),
            'import_types': m.Misc.query.filter(m.Misc.type == 'import_type')
        }

        res = {}

        request_type = args.get('type')
        if request_type:
            attr_list = request_type.split(',')
            try:
                for attr in attr_list:
                    res[attr] = _map_queries[attr].all()
            except KeyError as e:
                raise exc.BadRequestException('%s is not a valid type' % e)
        else:
            for key, query in _map_queries.items():
                res[key] = query.all()

        return res
