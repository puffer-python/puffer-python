from sqlalchemy import text

from catalog import models
from catalog.extensions.exceptions import BadRequestException
from catalog.models import db


class SqlUtils:
    @staticmethod
    def validate_duplicate_field(model_table, column, value, message):
        cln = getattr(model_table, column) if type(column) is str else column
        if model_table.query.filter(cln == value).first():
            raise BadRequestException(message)
