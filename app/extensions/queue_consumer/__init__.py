# coding=utf-8
""" Cung cấp tính năng thực hiện việc subscribing message queue và gọi hàm xử
lý tương ứng trong code.

Cách làm như sau:

Lắng nghe trên message queue, với mỗi message nhận được:
  1. Gọi hàm xử lý message: thông qua Blinker Signal
  2. Nếu mọi thứ OK (không Exception): lưu trạng thái msg trả về thành công,
  gửi ACK tới rabbitmq.
  3. Nếu mọi thứ không OK (Có Exception): lưu log msg vào db

"""
import logging
import rabbitpy
from sqlalchemy import orm

from catalog import models as m
from catalog import utils
from catalog.extensions.sqlalchemy_utils import json_encode

from .message_processor import MessageProcessor

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class QueueConsumer(object):
    """
    Thực hiện lắng nghe msgqueue
    """
    def __init__(self, amqp_url, queue_name, debug=False):
        """
        Tạo 1 đối tượng QueueConsumer kết nối tới rabbitmq và lắng nghe msg
        trên queue_name

        :param amqp_url: rabbitmq connection string
        :param queue_name: queue name
        :param debug: forward exception
        """
        self._amqp_url = amqp_url
        self._queue_name = queue_name
        self._debug = debug

    def _save_message_to_db(self, msg, queue_name):
        """ Lưu msg vào DB.

        :param msg:
        :param queue_name:
        :return:
        """
        def ensure_str(s):
            return s.decode() if isinstance(s, (bytes, bytearray)) else s

        msg_log = m.MsgLog(
            routing_key=msg.routing_key,
            exchange=msg.exchange,
            queue=queue_name or self._queue_name,
            status=m.MsgLog.Status.init,
            body_raw=ensure_str(msg.body),
            properties=json_encode(
                utils.rabbitmq_properties_to_dict(msg.properties)
            )
        )

        # create another session to manage the msg_log
        session_maker = orm.sessionmaker(bind=m.db.engine)
        session = session_maker()
        session.add(msg_log)
        session.commit()

        msg_id = msg_log.id
        session.close()
        return msg_id

    def _on_msg_received(self, msg, queue_name=None):
        """
        Xử lý khi nhận được 1 message từ RabbitMQ.

        :param rabbitpy.message.Message msg:
        :param queue_name:
        :return:
        """
        msg_id = self._save_message_to_db(
            msg,
            queue_name=queue_name or self._queue_name
        )
        msg.ack()

        message_processor.MessageProcessor.process_message(
            msg_id=msg_id,
            queue_name=queue_name,
            debug=self._debug
        )

    def run(self):
        """
        Lắng nghe và bắn signal.

        :return:
        """
        with rabbitpy.Connection(self._amqp_url) as conn:
            with conn.channel() as channel:
                queue = rabbitpy.Queue(channel, self._queue_name)

                # Consume msg
                for message in queue:
                    _logger.info('Received message:\n%s\n%s\n%s' % (
                        message.routing_key,
                        message.properties,
                        message.body,
                    ))
                    self._on_msg_received(
                        msg=message,
                        queue_name=queue.name
                    )
