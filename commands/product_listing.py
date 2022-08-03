# coding=utf-8
import logging

from catalog import app
from catalog.models import SellableProduct

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@app.cli.command()
def product_listing():
    """
    Need to delete
    """
    pass
