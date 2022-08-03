# coding=utf-8
import logging
from catalog import app


logger = logging.getLogger(__name__)


@app.cli.command('run-ram-consumer')
def run_ram_consumer():
    from catalog.extensions.ram.consumer import ram_consumer

    logger.info('START ram consumers...')
    ram_consumer.consume(app.config['RAM_KAFKA_BOOTSTRAP_SERVER'], app.config['RAM_KAFKA_CONSUMER_GROUP_NAME'])
