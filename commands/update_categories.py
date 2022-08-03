# coding=utf-8
import logging
from catalog import app
from catalog import models
from sqlalchemy import text
from catalog.services.categories import CategoryService

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


__VNPAY_SHOP_SELLER_ID = 2


@app.cli.command()
def update_old_code_categories():
    """Set prefix OLD- to code"""
    sql = f'UPDATE categories set code = CONCAT("OLD-", code) WHERE seller_id = {__VNPAY_SHOP_SELLER_ID}'
    models.db.session.execute(text(sql))
    models.db.session.commit()


@app.cli.command()
def update_old_name_categories():
    """Set prefix OLD- to name"""
    service = CategoryService.get_instance()
    categories = models.Category.query.filter(
        models.Category.seller_id == __VNPAY_SHOP_SELLER_ID,
        models.Category.name.notlike('OLD-%'))
    for c in categories:
        service.update_category({'name': f'OLD-{c.name}'}, c.id)
