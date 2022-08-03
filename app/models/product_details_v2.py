# coding=utf-8
import logging

from catalog.models import db
from catalog import models as m

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


class ProductDetailsV2(db.Model, m.TimestampMixin):
    """
    Lưu mô tả sản phẩm version 2
    """
    __tablename__ = 'product_details_v2'

    sku = db.Column(db.String(255))
    seller_sku = db.Column(db.String(255))
    uom_code = db.Column(db.String(255))
    uom_name = db.Column(db.String(255))
    uom_ratio = db.Column(db.Float())
    seller_id = db.Column(db.Integer())
    seller = db.Column(db.Text)
    provider = db.Column(db.Text)
    product_line = db.Column(db.Text)
    name = db.Column(db.String(500))
    url = db.Column(db.String(255))
    barcode = db.Column(db.String(255))
    barcodes = db.Column(db.Text)
    shipping_types = db.Column(db.String(500))
    type = db.Column(db.String(255))
    tax = db.Column(db.String(1000))
    images = db.Column(db.Text)
    display_name = db.Column(db.String(255))
    attribute_set = db.Column(db.String(255))
    attributes = db.Column(db.Text)
    categories = db.Column(db.Text)
    seller_categories = db.Column(db.Text)
    brand = db.Column(db.String(1000))
    status = db.Column(db.String(1000))
    smart_showroom = db.Column(db.String(1000))
    color = db.Column(db.Text)
    seo_info = db.Column(db.Text)
    warranty = db.Column(db.String(1000))
    tags = db.Column(db.String(1000))
    is_bundle = db.Column(db.Boolean)
    bundle_products = db.Column(db.Text)
    parent_bundles = db.Column(db.Text)
    channels = db.Column(db.Text)
    attribute_groups = db.Column(db.Text)
    product_group = db.Column(db.Text)
    terminals = db.Column(db.Text)
    manufacture = db.Column(db.Text)
    platform_categories = db.Column(db.Text)
    serial_managed = db.Column(db.Boolean)
    serial_generated = db.Column(db.Boolean)
    terminal_groups = db.Column(db.String(1000))
    sku_created_at = db.Column(db.String(255))
    created_by = db.Column(db.String(255))
    updated_by = db.Column(db.String(255))

    __table_args__ = (
        db.Index('IDX_product_details_v2__sku', sku),
        db.Index('IDX_product_details_v2__seller_sku', seller_sku),
    )
