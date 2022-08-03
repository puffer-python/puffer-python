import logging
from threading import Thread
from typing import List

from library.pyram.factory.receiver import ReceiverFactory
from library.pyram.common.thread import create_handle_message_thread
from library.pyram.common.thread import create_metric_thread
from library.pyram.common.thread import create_kafka_retry_threads

from catalog.extensions.ram.handlers import handler_registry


logger = logging.getLogger(__name__)


class RAMConsumer:
    _instance = None


    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RAMConsumer, cls).__new__(cls)
        return cls._instance

    def consume(self, ram_kafka_bootstrap_server, consumer_group_name):
        consume_threads: List[Thread] = []
        retry_threads: List[Thread] = []

        for handler in handler_registry.handlers.values():
            try:
                consumer = ReceiverFactory.create_kafka_receiver(
                    conn_str=ram_kafka_bootstrap_server,
                    message=handler.proto_message,
                    handler=handler.handler,
                    retry_handler=handler.retry_handler,
                    enable_retry=True,
                    enable_dlq=True,
                    retry_configs=[('3s', 3), ('10s', 10)],
                    consumer_group_name=consumer_group_name,
                )
            except Exception as e:
                logger.error(f'error when create RAM kafka consumer {ram_kafka_bootstrap_server}: {e}')
            else:
                consume_thread = create_handle_message_thread(service=consumer)
                consume_threads.append(consume_thread)

                _retry_threads = create_kafka_retry_threads(service=consumer)
                retry_threads.append(_retry_threads)

        for thread in consume_threads:
            thread.join()
        for thread in retry_threads:
            thread.join()

        metric_thread = create_metric_thread()
        metric_thread.join()


ram_consumer = RAMConsumer()
