import logging

import pika

__author__ = 'Nam.VH'
_logger = logging.getLogger(__name__)

from catalog import app


class QueuePublisher(object):
    def __init__(self, exchange=None, debug=False):
        """
        Init the object
        :param amqp_url: rabbitmq connection string
        :param exchange: queue name
        :param debug: forward exception
        """
        self._amqp_url = app.config['TEKO_AMQP_URL']
        self._exchange = app.config.get('CATALOG_EXCHANGE', 'teko.catalog')

    def publish_message(self, message=None, routing_key=None, headers=None):
        connection = pika.BlockingConnection(pika.URLParameters(self._amqp_url))
        channel = connection.channel()
        properties = pika.BasicProperties(
            app_id='catalog-service',
            headers=headers
        )
        channel.basic_publish(
            exchange=self._exchange,
            routing_key=routing_key,
            body=message,
            properties=properties
        )
        connection.close()
