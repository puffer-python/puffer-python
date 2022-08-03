# coding=utf-8
import logging
import requests
from datetime import datetime
from flask import current_app as app
from flask_login import current_user

from catalog import utils, models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


def update_price_for_skus(products):
    """
    Call PPM API to update price for a list of sku
    :param products:
    :return:
    """
    status_code = call_ppm_api(products)
    if status_code == 200:
        return products, 'Tạo SKU thành công'

    for product in products:
        product.sale_price = None
        product.supplier_sale_price = None

    m.db.session.commit()
    return products, 'Tạo SKU thành công, thiết lập giá vui lòng thử lại sau'


def call_ppm_api(products):
    def generate_payload_for_sku(product):
        """

        :param product:
        :return:
        """
        return [
            {
                'type': 'sell_price',
                'value': product.sale_price,
                'sku': product.sku,
                'start': datetime.strftime(product.created_at, '%d/%m/%Y'),
                'end': None
            },
            {
                'type': 'supplier_sale_price',
                'value': product.supplier_sale_price,
                'sku': product.sku,
                'start': datetime.strftime(product.created_at, '%d/%m/%Y'),
                'end': None
            }
        ]

    payload = utils.flatten_list(
        [generate_payload_for_sku(product) for product in products]
    )
    res = requests.post(
        url=app.config['PPM_BATCH_PRICE_SCHEDULE_API'],
        json={
            'schedules': payload
        },
        headers={
            "Content-Type": "application/json",
            "Authorization": current_user.access_token
        },
        verify=False
    )
    _logger.info(f'Call API {app.config["PPM_BATCH_PRICE_SCHEDULE_API"]} with payload {payload}')
    _logger.info(f'API {app.config["PPM_BATCH_PRICE_SCHEDULE_API"]} return {res.status_code}')

    return res.status_code
