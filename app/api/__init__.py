# coding=utf-8
import logging
import flask_restplus as _fr
from flask import Blueprint
from catalog.extensions.exceptions import global_error_handler
from ._base import (
    ListParamBase,
    ListResponseBase,
    SortableParam,
    extract_hyper_param_from_list_request,
    make_pagination_response,
)
from . import (
    product,
    brand,
    master_category,
    sale_category,
    extra,
    imports,
    attribute,
    attribute_set,
    category,
    master_data,
    taxes,
    unit,
    shipping_policy,
    shipping_type
)
from .manufacture import manufacture_ns

__author__ = 'dung.bv@teko.vn'

_logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)
api = _fr.Api(
    app=api_bp,
    version='1.0',
    title='Catalog API',
    description=(
        "It is API for Catalog Service"
    ),
    validate=True,
    doc='/swagger'
)


def init_app(app, **kwargs):
    """
    Extension initialization point
    :param flask.Flask app: the app
    :param kwargs:
    :return:
    """
    app.register_blueprint(api_bp)
    api.add_namespace(product.product_ns)
    api.add_namespace(product.variant_ns)
    api.add_namespace(product.sellable_ns)
    api.add_namespace(product.sku_ns)
    api.add_namespace(product.detail_sku_ns)
    api.add_namespace(brand.brand_ns)
    api.add_namespace(master_category.master_category_ns)
    api.add_namespace(sale_category.sale_category_ns)
    api.add_namespace(extra.extra_ns)
    api.add_namespace(extra.old_extra_ns)
    api.add_namespace(imports.import_ns)
    api.add_namespace(attribute.attribute_ns)
    api.add_namespace(attribute_set.attribute_set_ns)
    api.add_namespace(category.category_ns)
    api.add_namespace(taxes.tax_ns)
    api.add_namespace(master_data.master_data_ns)
    api.add_namespace(unit.unit_ns)
    api.add_namespace(shipping_policy.shipping_policy_ns)
    api.add_namespace(shipping_type.shipping_type_ns)
    api.add_namespace(manufacture_ns)

    api.error_handlers[Exception] = global_error_handler
