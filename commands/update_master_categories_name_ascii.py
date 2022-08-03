# coding=utf-8
import logging

from catalog import app

__author__ = 'Quang.LM'

from catalog.models import MasterCategory, db
from catalog import utils

_logger = logging.getLogger(__name__)


@app.cli.command()
def update_master_categories_name_ascii():
    """Update name_ascii of master_categories table"""

    categories = MasterCategory.query.all()

    for category in categories:
        category.name_ascii = utils.remove_accents(category.name)

    db.session.commit()
