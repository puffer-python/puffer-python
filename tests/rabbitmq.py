# coding=utf-8
import logging
import rabbitpy
from unittest import mock

from catalog.extensions import queue_consumer
from catalog.extensions.sqlalchemy_utils import json_encode

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


def build_message(routing_key, body, properties=None, exchange=None):
    """ Giả lập dữ liệu cho 1 message nhận được.

    :param str routing_key: routing key của message
    :param dict[str, str]|str body: msg's body
    :param dict[str, str] properties: msg's properties
    :param string exchange: msg's exchange name

    :return: message được giả lập
    :rtype: rabbitpy.Message
    """
    connection = mock.MagicMock('rabbitpy.connection.Connection')
    connection._io = mock.Mock()
    connection._io.write_trigger = mock.Mock('socket.socket')
    connection._io.write_trigger.send = mock.Mock()
    connection._channel0 = mock.Mock()
    connection._channel0.properties = {}
    connection._events = rabbitpy.events.Events()
    connection._exceptions = rabbitpy.connection.queue.Queue()
    connection.open = True
    connection.closed = False
    channel = rabbitpy.channel.Channel(
        1,
        {},
        connection._events,
        connection._exceptions,
        rabbitpy.connection.queue.Queue(),
        rabbitpy.connection.queue.Queue(),
        32768,
        connection._io.write_trigger,
        connection=connection
    )
    channel._set_state(channel.OPEN)

    method_frame = mock.MagicMock()
    method_frame.routing_key = routing_key
    method_frame.exchange = exchange or 'dummy-exchange'

    body = body if isinstance(body, (str, bytes)) else json_encode(body)

    msg = rabbitpy.Message(
        channel,
        body_value=body,
        properties=properties or {}
    )
    msg.method = method_frame
    return msg


def simulate_message(routing_key, body, properties=None, queue_name=None,
                     exchange=None, debug=True):
    """ Giả lập việc nhận được 1 message từ RabbitMQ và
    kích hoạt các quá trình liên quan đến message này

    :param str routing_key: routing key của message
    :param dict[str, str] body: msg's body
    :param dict[str, str] properties: msg's properties
    :param str queue_name: tên queue mà msg này chứa trong đó
    :param string exchange: msg's exchange name
    :param bool debug: Có forward exception ra ngoài hay không?

    :return: Trả về message vừa được lưu vào DB với việc mô phỏng
    :rtype: locore.models.ReceivedMsg
    """
    msg = build_message(routing_key, body, properties)
    consumer = queue_consumer.QueueConsumer(
        amqp_url=None,
        queue_name=queue_name or 'teko.catalog',
        debug=debug
    )
    consumer._on_msg_received(msg)
