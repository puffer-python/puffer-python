# coding=utf-8
import logging
from catalog import app
from catalog import models
from sqlalchemy import text

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


@app.cli.command()
def set_not_display_with_unit_and_size_attribute():
    """Set unit, size attribute to not display"""
    models.db.session.execute(text(
        'UPDATE attribute_group_attribute set is_displayed = 0 WHERE EXISTS '
        '(SELECT 1 from attributes WHERE attributes.id = attribute_group_attribute.attribute_id '
        'AND attributes.code IN ("weight","length","width","height","pack_weight","pack_length","pack_width","pack_height", "uom", "uom_ratio"))'

    ))
    models.db.session.commit()
