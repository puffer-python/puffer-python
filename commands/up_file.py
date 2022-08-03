# coding=utf-8
import logging
from catalog import app

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


@app.cli.command()
def up_file():
    pass
