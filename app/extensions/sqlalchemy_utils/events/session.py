# coding=utf-8
import logging
from flask import g
from sqlalchemy import event
from flask_login import current_user

from catalog.models import db
from catalog.models import MasterCategory
from catalog import utils

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@event.listens_for(db.session, 'after_flush')
def receive_after_flush(session, flush_ctx):
    """
    Perform event handling logic

    :param session:
    :param flush_ctx:
    :return:
    """
    transaction_change = [e for e in session.dirty if isinstance(e, db.Model)]

    if not transaction_change:
        return

    pass

    # for element in transaction_change:
    #     if hasattr(element, 'created_by') and element.created_by is None:
    #         element.created_by = current_user.email
    #     elif hasattr(element, 'updated_by'):
    #         element.updated_by = current_user.email


@event.listens_for(MasterCategory.name, 'set')
def set_name_handler(target, value, oldvalue, initiator):
    target.name_ascii = utils.remove_accents(value)
