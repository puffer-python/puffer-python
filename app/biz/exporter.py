# coding=utf-8
import uuid
import config
import logging
import requests

from catalog import celery
from catalog.constants import ExportSellable
from catalog.extensions import signals
from catalog.services.products.sellable import (sellables_export_query_builder, detail_sellables_exporter,
                                                sellables_exporter, seo_info_exporter)

__logger = logging.getLogger(__name__)

__author = 'Dung.BV'


@signals.on_export_product
def signal_export_product(params):
    sellables_export_task.delay(**params)


@celery.task
def sellables_export_task(params, export_type=None, email=None):
    query = sellables_export_query_builder(params, export_type)
    out = None
    if export_type == ExportSellable.EXPORT_ALL_ATTRIBUTE:
        attribute_set_id = params.get('attribute_set')
        out = detail_sellables_exporter(query, attribute_set_id)
    elif export_type == ExportSellable.EXPORT_GENERAL_INFO:
        out = sellables_exporter(query)
    elif export_type == ExportSellable.EXPORT_SEO_INFO:
        out = seo_info_exporter(query)
    url = upload_export_file(out)
    send_email(url, email)


def upload_export_file(file):
    """Upload importing result to file service"""
    upload_form = {'file': (
        f'{uuid.uuid4()}.xlsx',
        file,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )}
    resp = requests.post('{}/upload/doc'.format(config.FILE_API), files=upload_form)
    if resp.status_code != 200:
        raise RuntimeError('Result file can not upload to server')
    return resp.json().get('url')


def send_email(url, email):
    body_request = {
        "templateId": config.NOTI_SERVICE_DOMAIN.get('TemplateId'),
        "brand": config.NOTI_SERVICE_DOMAIN.get('Brand'),
        "isBroadcast": False,
        "receivers": [
            {
                "email": email,
                "messageParams": [
                    {
                        "code": "title",
                        "value": "Kết quả export sản phẩm"
                    },
                    {
                        "code": "content",
                        "value": "Export dữ liệu thành công. Vui lòng tải kết quả Export sản phẩm tại {}".format(url)
                    }
                ]
            }
        ]
    }
    token = config.NOTI_SERVICE_DOMAIN.get('Token')
    resp = requests.post("{}/{}".format(config.NOTI_SERVICE_DOMAIN.get('Domain'), '/api/v1/send-message'),
                         json=body_request, headers={
            'Authorization': f'Bearer {token}'
        })
    if resp.status_code != 200:
        __logger.exception(resp)
        raise RuntimeError('Result file can not upload to server')
    return resp.json().get('url')
