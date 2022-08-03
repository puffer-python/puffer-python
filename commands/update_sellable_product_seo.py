# coding=utf-8
import logging

from catalog import app
from catalog import models
from sqlalchemy import text

__author__ = 'Quang.LM'

_logger = logging.getLogger(__name__)


@app.cli.command()
def update_url_key_sellable_product_seo_terminal():
    """Update url_key of sellable_product_seo_info_terminal table"""

    models.db.session.execute(text(
        'UPDATE sellable_product_seo_info_terminal left join sellable_products on sellable_products.id = sellable_product_seo_info_terminal.sellable_product_id'
        ' left join product_variants on product_variants.id = sellable_products.variant_id'
        ' SET sellable_product_seo_info_terminal.url_key = product_variants.url_key'

    ))
    models.db.session.commit()
