# coding=utf-8
import logging

from catalog import app
from catalog.extensions import queue_consumer

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@app.cli.command()
def subscribe_teko_queue():
    """Subcrible queue from teko RabbitMQ"""
    queue_name = app.config.get('TEKO_QUEUE_NAME', 'teko.seller')
    amqp_url = app.config['TEKO_AMQP_URL']

    consumer = queue_consumer.QueueConsumer(
        amqp_url=amqp_url,
        queue_name=queue_name
    )
    _logger.info('Subscribe TEKO queue at %s' % app.config['AMQP_HOST'])
    consumer.run()
