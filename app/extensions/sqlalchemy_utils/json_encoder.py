# coding=utf-8
import logging
import flask
import decimal
import datetime
import enum
import json
from unittest import mock


__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class JSONEncoder(flask.json.JSONEncoder):
    """Customized flask JSON Encoder"""

    def default(self, o):
        from catalog.models import db
        if hasattr(o, '__json__'):
            return o.__json__()
        if isinstance(o, decimal.Decimal):
            if o == o.to_integral_value():
                return int(o)
            else:
                return float(o)
        if isinstance(o, (datetime.datetime, datetime.date)):
            return o.isoformat(sep=' ')
        if isinstance(o, enum.Enum):
            return o.value
        if isinstance(o, tuple):
            return list(o)
        if isinstance(o, db.Model):
            fields = {}
            for f in dir(o):
                if not f.startswith('_') and f != 'metadata':
                    data = getattr(o, f)
                    try:
                        json.dumps(data)
                        fields[f] = data
                    except TypeError:
                        fields[f] = None
            return fields
        if isinstance(o, mock.MagicMock):
            return repr(o)
        return super().default(o)


_default_json_encoder = JSONEncoder()
json_encode = _default_json_encoder.encode
