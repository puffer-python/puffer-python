# coding=utf-8
import logging

from catalog import app

__author__ = 'Quang.LM'

from catalog.models import db
from sqlalchemy import text

_logger = logging.getLogger(__name__)


__GOOGLE_FILE_STORAGE = 'https://storage.googleapis.com/teko-gae.appspot.com'


@app.cli.command()
def update_brand_logo_path():
    """Update path to full path of brands table"""

    db.session.execute(text(
        f'UPDATE brands set path = CONCAT("{__GOOGLE_FILE_STORAGE}", path), updated_at = NOW(), updated_by="quanglm"'
        ' where path != "" and path is not null'
        ' AND path not like "https://%" AND path not like "http://%" AND path like "/%"'
    ))

    db.session.execute(text(
        f'UPDATE brands set path = CONCAT("{__GOOGLE_FILE_STORAGE}/", path), updated_at = NOW(), updated_by="quanglm"'
        ' where path != "" and path is not null'
        ' AND path not like "https://%" AND path not like "http://%" AND path not like "/%"'
    ))

    db.session.commit()
