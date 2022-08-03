# coding=utf-8
import logging
from catalog import app

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


@app.cli.command()
def sync_product():
    """Re-sync product for Fahasa """
    pass
