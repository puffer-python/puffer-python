# coding=utf-8
import logging
import enum
from flask import request
from sqlalchemy import event

from catalog import models as m
from catalog.extensions.sqlalchemy_utils.json_encoder import json_encode

from .schema import common_schema

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


def clear_redundant(x):
    """
    Xóa đi thông tin dư thừa, phục vụ cho việc lưu ra json format
    :param x:
    :return:
    """
    if x.__class__.__name__ in ['list', 'InstrumentedList']:
        return str([clear_redundant(e) for e in x])
    elif issubclass(x.__class__, enum.Enum):
        return str(x.value)
    else:
        return str(x)


@event.listens_for(m.db.session, 'after_flush')
def receive_after_flush(session, flush_context):
    """
    Bắt sự kiện after flush để lưu log thay đổi của models.

    :param session:
    :param flush_context:
    :return:
    """

    def loggable(obj):
        if hasattr(obj, '_log'):
            return obj._log
        return True

    transaction_change = [e for e in session.dirty if loggable(e)]

    if not transaction_change:
        return

    for element in transaction_change:
        sqlalchemy_dict = element.__dict__
        dict_attr = {}

        # Xóa phần dư thừa
        for key in sqlalchemy_dict.keys():
            if key == '_sa_instance_state':
                continue
            dict_attr[str(key)] = clear_redundant(sqlalchemy_dict[key])

        object_id = element.id
        object_type = str(element.__class__.__name__)
        try:
            action = request.method
        except RuntimeError:
            action = 'IMPORT'
        data = json_encode(dict_attr)

        action_log = m.ActionLog(
            action=action,
            object=object_type,
            object_id=object_id,
            object_data=data
        )  # type: m.ActionLog

        m.db.session.add(action_log)


def log_edit_product(product, user=None):
    """
    @Todo
    :param product:
    :param user:
    :return:
    """
    pass
