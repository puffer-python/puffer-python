import logging
from catalog import app
from catalog.extensions.ram_queue_consumer import run_default_consumer, run_push_push_product_data_consumer, \
    run_update_product_detail_consumer, run_update_product_detail_v2_consumer

__author__ = 'phuong.h'
_logger = logging.getLogger(__name__)


@app.cli.command()
def subscribe_ram_queue_default():
    run_default_consumer()


@app.cli.command()
def subscribe_ram_queue_push_product_data():
    run_push_push_product_data_consumer()


@app.cli.command()
def subscribe_ram_queue_update_product_detail():
    run_update_product_detail_consumer()


@app.cli.command()
def subscribe_ram_queue_update_product_detail_v2():
    run_update_product_detail_v2_consumer()
