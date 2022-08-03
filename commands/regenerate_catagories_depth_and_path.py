# coding=utf-8
import logging

from catalog import app
from catalog.extensions import queue_consumer, signals

__author__ = 'Minh.ND'

from catalog.models import Category, db

_logger = logging.getLogger(__name__)


@app.cli.command()
def regenerate_categories():
    """Regenerate depth and path of categories table"""

    ancestor_table = {}
    categories = Category.query.all()

    for category in categories:
        ancestor_table[category.id] = category.parent_id

    for category in categories:
        depth = 0
        path = ''

        current_id = category.id
        while current_id != 0:
            if path == '':
                path += str(current_id)
            else:
                path = str(current_id) + '/' + path

            depth += 1
            if ancestor_table.get(current_id) is None:
                break

            current_id = ancestor_table[current_id]

        if current_id != 0 and ancestor_table.get(current_id) is None:
            continue

        category.depth = depth
        category.path = path

    db.session.commit()



