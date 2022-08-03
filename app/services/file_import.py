# coding=utf-8
import logging
import math
import os
import pathlib
import time
import requests
import config

from flask import abort
from catalog import models as m
from random import randint
from catalog.services import extra

from werkzeug.utils import secure_filename

from catalog.models import db
from catalog.extensions import signals
from catalog.extensions import exceptions as excs

__author__ = 'Thiem.nv'
_logger = logging.getLogger(__name__)


def validate_data(**kwargs):
    # check start date <= end date
    start_at = kwargs.get('start_at')
    end_at = kwargs.get('end_at')

    if start_at and end_at and start_at > end_at:
        abort(400, 'Invalid date range')

    # check wrong status code
    status = kwargs.get('status')
    if status and status not in ['new', 'processing', 'done']:
        abort(400, 'status is not defined')

    # check wrong type code
    types = kwargs.get('type')



def get_import_history(**kwargs):
    """
    Trả về danh sách lịch sử import dựa theo các dữ liệu truyền vào, đồng thời
    trả về các tham số dùng để phân trang

    Dữ liệu trả về có dạng:
    {
        code: 'SUCCESS',
        message: 'any',
        result: {
            'current_page': int,
            'page_size': int,
            'total_items': int,
            'history_list': list[m.FileImport]
        }
    }

    :param kwargs: filter variables
    :return: list of file import
    """

    validate_data(**kwargs)

    list_query = ImportHistoryQuery()
    list_query.apply_filter(**kwargs)

    page = kwargs.get('page', 0)
    page_size = kwargs.get('pageSize', 10)
    total_records = len(list_query)
    max_page = math.ceil(total_records / page_size)

    if total_records > 0 and page > max_page:
        abort(400, 'Invalid page number')

    list_query.paginate(page, page_size)

    history_list = list(list_query)

    return {
        'code': 'SUCCESS',
        'message': 'Get history list successfully',
        'result': {
            'current_page': page,
            'page_size': page_size,
            'total_items': total_records,
            'history_list': history_list
        }
    }


class ImportHistoryQuery(object):
    """
    Query lịch sử import theo bộ filter
    """

    def __init__(self):
        self.query = m.FileImport.query

    def __len__(self):
        """
        Trả về số lượng bản ghi tìm thấy
        :return:
        :rtype: int
        """
        return self.query.count()

    def __iter__(self):
        """
        Yield danh sách kênh bán tìm thấy
        :return:
        :rtype: list[models.SaleChannel]
        """
        yield from self.query

    def apply_filter(self, **kwargs):
        """
        Filter theo các điều kiện được truyền vào, bao gồm:
            - Kiểu import (product, attribute, ...)
            - Trạng thái import (chờ xử lý, hoàn tất, ...)
            - Khoảng thời gian upload file (từ ngày ... đến ngày ...)

        :param kwargs:
        :return:
        """
        seller = {}
        seller_id = seller.get('sellerId')

        if seller_id is not None:
            self.query = self.query.filter(
                m.FileImport.seller_id == seller_id
            )
        else:
            abort(400, 'Seller does not exist')

        import_type = kwargs.get('type')
        if import_type:
            self._apply_import_type_filter(import_type)

        status = kwargs.get('status')
        if status:
            self._apply_status_filter(status)

        start_at = kwargs.get('start_at')
        if start_at:
            self._apply_start_at_filter(start_at)

        end_at = kwargs.get('end_at')
        if end_at:
            self._apply_end_at_filter(end_at)

        sort_order = kwargs.get('sort_order')
        if sort_order:
            self._apply_created_at_order(sort_order)

    def _apply_import_type_filter(self, import_type):
        import_type = import_type.split(',')
        self.query = self.query.filter(
            m.FileImport.type.in_(['{}'.format(el) for el in import_type])
        )

    def _apply_status_filter(self, status):
        self.query = self.query.filter(
            m.FileImport.status == '{}'.format(status))

    def _apply_start_at_filter(self, start_at):
        self.query = self.query.filter(
            m.FileImport.created_at >= '{} 00:00:00'.format(start_at))

    def _apply_end_at_filter(self, end_at):
        self.query = self.query.filter(
            m.FileImport.created_at <= '{} 23:59:59'.format(end_at))

    def _apply_created_at_order(self, order):
        if order == 'desc':
            self.query = self.query.order_by(m.FileImport.created_at.desc())
        else:
            self.query = self.query.order_by(m.FileImport.created_at.asc())

    def paginate(self, page, page_size):
        """
        Apply pagination params to sale channel list query
        :param page:
        :param page_size:
        :return:
        """
        page = page - 1 if page > 0 else 0
        self.query = self.query.offset(page * page_size).limit(page_size)


def _move_file(file):
    send_file = {'file': (file.filename, file.read(), file.mimetype)}
    r = requests.post(
        os.getenv('UPLOAD_FILE_DOC_URL', 'https://catalog.services.teko.vn/upload/doc'),
        files=send_file,
    )
    if r.status_code == 200:
        return r.json().get('url')
    raise excs.BadRequestException(r.json().get('message'))


def send_task(data):
    signals.product_import_signal.send(data)




