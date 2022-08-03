# coding=utf-8
import logging
import enum
from flask import request
from flask_login import current_user
from sqlalchemy import event
import sqlalchemy as sa
import json
from catalog import models as m
from catalog.extensions.sqlalchemy_utils.json_encoder import json_encode
import flask_login

from catalog.utils import dict_diff
from .schema import common_schema

import copy

__author__ = 'Shyaken'
_logger = logging.getLogger(__name__)

# coding=utf-8


def clear_redundant(x):
    """
    Xóa đi thông tin dư thừa, phục vụ cho việc lưu ra json format
    :param x:
    :return:
    """
    if x.__class__.__name__ == 'list' or x.__class__.__name__ == 'InstrumentedList':
        return str([clear_redundant(e) for e in x])
    elif issubclass(x.__class__, enum.Enum):
        return str(x.value)
    else:
        return str(x)


def save_log_product_change(product_change, user_email):
    for element in product_change:
        ins_element = sa.inspect(element)
        committed_state = ins_element.committed_state

        # Trạng thái from và to của object
        from_state = {}
        to_state = {}
        tracking_fields = ['data']

        for key in committed_state.keys():
            if key in tracking_fields:
                from_state[str(key)] = committed_state[key]
                to_state[str(key)] = eval('element.' + str(key))

        for key in from_state.keys():
            from_state[key] = clear_redundant(from_state[key])
            to_state[key] = clear_redundant(to_state[key])

        if not to_state and not from_state:
            continue

        data_changes = dict_diff(from_state, to_state)
        sku = element.sku

        log = m.ProductLog(
            user_email=user_email,
            sku=sku,
            old_data=json.dumps(from_state),
            new_data=json.dumps(to_state),
            changes=json.dumps(data_changes)
        )
        m.db.session.add(log)
        m.db.session.flush()

    m.db.session.commit()


def save_log_product_new(product_new, user_email):
    for element in product_new:
        sqlalchemy_dict = element.__dict__
        dict_attr = {}

        # Xóa phần dư thừa lưu vào log
        for key in sqlalchemy_dict.keys():
            dict_attr[str(key)] = clear_redundant(sqlalchemy_dict[key])

        sku = element.sku
        data_changes = json.dumps(dict_attr)

        log = m.ProductLog(
            user_email=user_email,
            sku=sku,
            old_data=None,
            new_data=data_changes,
            chages=data_changes
        )
        m.db.session.add(log)
        m.db.session.flush()
    m.db.session.commit()


def handle_saving_log(session, flush_context):
    user_email = None
    product_log = ['ProductDetail']

    # Log for product
    product_change = [e for e in session.dirty if e.__class__.__name__ in product_log]
    product_new = [e for e in session.new if e.__class__.__name__ in product_log]
    # transaction_deleted = [e for e in session.deleted if e.__class__.__name__ == 'TransportNew']

    if len( product_change + product_new ) == 0:
        return

    try:
        if current_user:
            user_email = flask_login.current_user.email
    except AttributeError as ex:
        _logger.exception(ex)
        user_email = None

    '''
    ProductDetail thay đổi
    '''
    save_log_product_change(product_change, user_email)

    '''
    ProductDetail được thêm vào --------------------------------------------------------------------------
    '''
    save_log_product_new(product_new, user_email)


@event.listens_for(m.db.session, 'after_flush')
def receive_after_flush(session, flush_context):
    '''
    Hàm bắt sự kiện after_flush kiểm tra sự thay đổi liên quan đến bảng product_details để lưu log

    :param session:
    :param flush_context:
    :param instances:
    :return:
    '''
    # Vẫn cho phép lưu cột user_id null vì có thể thao tác đó do một API chưa được cấp quyền
    # Warning: user ở đây là một object của 'werkzeug.local.LocalProxy' (dù không có cũng không phải None)
    handle_saving_log(session, flush_context)

