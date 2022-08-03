# coding=utf-8
import logging
import json
import traceback
from werkzeug import local
from sqlalchemy import orm
from flask import current_app

from catalog import models as m
from catalog import biz

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)

_msgs_stack = local.LocalStack()

current_message = local.LocalProxy(lambda: _get_current_msg())


def _get_current_msg():
    return _msgs_stack.top


class MessageProcessor(object):
    """ Xử lý 1 ReceivedMessage. Log lại traceback exception + msg nếu có
    lỗi xảy ra.

    1. Gửi signal xử lý msg
    2. Nếu không có exception, chuyển trạng thái msg thành 'ok'
    3. Nếu có exception xảy ra:
        - Đổi trạng thái msg thành 'error'
        - Lưu traceback vào ReceivedMessage.log
        - Lưu exception vào ReceivedMesssage.error
    """

    def __init__(self, msg_id, queue_name, debug=False):
        """

        :param msg_id:
        :param queue_name:
        :param debug:
        """
        self.msg = m.MsgLog.query.get(msg_id)  # type: m.MsgLog
        self.queue_name = queue_name
        self.session_maker = orm.sessionmaker(bind=m.db.engine)
        self.session = self.session_maker()
        self._debug = debug

    def process(self):
        """

        :return:
        """
        if not self.msg:
            return

        _msgs_stack.push(self.msg)
        try:
            biz.teko_msg_signal.send(
                self.msg.routing_key,
                body=self.msg.body,
                properties=json.loads(self.msg.properties)  # msg properties
            )
        except Exception as e:
            _logger.exception(e)
            raise
        finally:
            _msgs_stack.pop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            traceback_info = traceback.format_exc()
            self.msg.error_message = repr(exc_val)
            self.msg.log = traceback_info
            self.msg.status = m.MsgLog.Status.failed

            self.session.commit()
            self.session.close()
        else:
            self.msg.status = m.MsgLog.Status.ok

        if not self._debug:
            return True

    @classmethod
    def process_message(cls, msg_id, queue_name, debug=False):
        """

        :param msg_id:
        :param queue_name:
        :param debug:
        :return:
        """
        with MessageProcessor(msg_id, queue_name, debug=debug) as processor:
            with current_app.app_context():
                processor.process()
