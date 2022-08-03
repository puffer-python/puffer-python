# coding=utf-8
from catalog.utils import safe_cast
import logging
import base64 as b64
import png
import requests
from flask import current_app
from sqlalchemy import or_, desc
from sqlalchemy.sql import func
from flask_login import current_user

from catalog import models as m
from catalog.extensions import signals
from catalog.extensions import exceptions as exc
from catalog.services import QueryBase

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)

BRAND_LOGO_SIZE = (1200, 500)


class BrandListQuery(QueryBase):
    model = m.Brand

    def apply_filters(self, params):
        kw = params.get('query')
        if kw:
            self._apply_keyword_filter(kw)

        ids = params.get('ids')
        if ids:
            self._apply_ids_filter(ids)

        codes = params.get('codes')
        if codes:
            self._apply_codes_filter(codes)

        is_active = params.get('is_active')
        if is_active is not None:
            self._apply_active_filter(is_active)

        approved_status = params.get('approved_status')
        if approved_status is not None:
            self._apply_approved_status_filter(approved_status)

        has_logo = params.get('has_logo')
        if has_logo is not None:
            self._apply_has_logo_filter(has_logo)

    def _apply_keyword_filter(self, kw):
        self.query = self.query.filter(or_(
            m.Brand.name.ilike('%{}%'.format(str(kw).lower())),
            m.Brand.code.like(f'%{kw}%')
        ))

    def _apply_ids_filter(self, ids):
        self.query = self.query.filter(
            m.Brand.id.in_(ids)
        )

    def _apply_codes_filter(self, codes):
        self.query = self.query.filter(
            m.Brand.code.in_(codes.split(','))
        )

    def _apply_active_filter(self, is_active):
        self.query = self.query.filter(
            m.Brand.is_active == is_active
        )

    def _apply_approved_status_filter(self, approved_status):
        self.query = self.query.filter(
            m.Brand.approved_status == approved_status
        )

    def _apply_has_logo_filter(self, has_logo):
        if not has_logo:
            self.query = self.query.filter(
                m.Brand.path.is_(None)
            )
        else:
            self.query = self.query.filter(
                m.Brand.path.isnot(None)
            )

    def _apply_sort_order(self):
        self.query = self.query.order_by(desc(m.Brand.updated_at))


def get_brand_list(**params):
    page = params.pop('page')
    page_size = params.pop('page_size')
    list_query = BrandListQuery()
    list_query.apply_filters(params)
    list_query.sort('updated_at', 'descend')
    total_records = len(list_query)
    list_query.pagination(page, page_size)

    return {
        'current_page': page,
        'page_size': page_size,
        'total_records': total_records,
        'brands': list_query.all()
    }


def get_brand(brand_id):
    """

    :param int brand_id:
    :return: a brand matched with id
    :rtype: m.Brand
    """
    brand = m.Brand.query.filter(
        m.Brand.id == brand_id
    ).first()
    if not brand:
        raise exc.BadRequestException(
            'Thuơng hiệu không tồn tại trên hệ thống'
        )

    return brand


def gen_code():
    last_brand = m.Brand.query.filter(
        m.Brand.code.isnot(None)
    ).order_by(
        m.Brand.id.desc()
    ).first()
    try:
        return 'TH{:06}'.format(
            int(last_brand.internal_code[2:]) + 1
        )
    except AttributeError:
        return 'TH000001'


def create_brand(data):
    brand = m.Brand()
    brand.name = data.get('name')
    brand.code = data.get('code')
    brand.doc_request = data.get('doc_request')
    brand.internal_code = gen_code()

    logo = data.get('logo')
    if logo:
        brand.path = save_logo_image(logo)

    m.db.session.add(brand)
    m.db.session.flush()
    signals.brand_created_signal.send(brand)
    m.db.session.commit()
    return brand


def __update_brand(brand, data):
    """update_brand

    :param brand:
    :param data:
    """
    if 'logo' in data:
        logo = data.pop('logo')
        REQUEST_DELETE_LOGO = logo is None
        if REQUEST_DELETE_LOGO:
            brand.path = None
        else:
            brand.path = save_logo_image(logo)
    is_change = brand.name != data.get('name')
    for key, value in data.items():
        if hasattr(brand, key):
            setattr(brand, key, value)

    if is_change:
        signals.brand_updated_signal.send(brand)
    m.db.session.commit()
    return brand


def update_brand(brand_id, data):
    """update_brand

    :param brand_id:
    :param data:
    """
    brand = m.Brand.query.filter(m.Brand.id == brand_id).first()
    __update_brand(brand, data)
    return brand


def update_brand_by_code(brand_code, data):
    """update_brand

    :param brand_id:
    :param data:
    """
    brand = m.Brand.query.filter(m.Brand.code == brand_code).first()
    if brand:
        __update_brand(brand, data)
    else:
        raise exc.BadRequestException(
            'Thuơng hiệu không tồn tại trên hệ thống'
        )
    return brand


def validate_image(b64_image):
    if ',' not in b64_image:
        raise exc.BadRequestException('Ảnh không phải b64')
    header, data = b64_image.split(',')
    png_reader = png.Reader(bytes=b64.b64decode(data))
    width, height, value, info = png_reader.read_flat()
    if not (width <= BRAND_LOGO_SIZE[0] and height <= BRAND_LOGO_SIZE[1]):
        raise exc.BadRequestException('Ảnh phải nhỏ hơn 1200 x 500')


def send_to_image_service(b64_image):
    file = b64.b64decode(b64_image.split(',')[1])
    resp = requests.post(
        url=current_app.config['FILE_API'] + '/upload/image',
        files={'file': ('lmao.png', file, 'image/png')}
    )
    if resp.status_code != 200:
        raise exc.BadRequestException('Lưu logo không thành công')
    return resp.json().get('url')


def save_logo_image(b64_image):
    """save_logo_image

    :param b64_image:
    :param code:
    """
    try:
        validate_image(b64_image)
        path = send_to_image_service(b64_image)
    except png.FormatError:
        raise exc.BadRequestException('File ảnh phải là ảnh PNG')
    except exc.HTTPException:
        raise
    except Exception as e:
        raise exc.BadRequestException(message='Lưu logo không thành công')
    else:
        return path
