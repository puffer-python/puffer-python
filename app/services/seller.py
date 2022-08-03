# coding=utf-8

import config
import logging
import requests


from catalog import models
from catalog.models import (
    db, Seller, PlatformSellers
)
from catalog.extensions.signals import platform_seller_upsert_created_signal
from catalog.extensions.flask_cache import cache

_MAX_PAGE_SIZE = 1000

_logger = logging.getLogger(__name__)


@cache.memoize(timeout=300)
def get_seller_by_id(seller_id: int) -> dict:
    """
    Get the seller info from the seller system
    Return a dict
    Param is a seller identify
    Cache: 300 seconds

    """
    url = f'{config.SELLER_API}/sellers/{seller_id}'
    try:
        resp = requests.get(url, timeout=2)
    except requests.Timeout:
        return {}
    else:
        return resp.json().get('result', {}).get('seller')


def get_default_platform_owner_of_seller(seller_id: int, session=None) -> int:
    try:
        conn = session or models.db.session
        owner_platform = conn.query(PlatformSellers).filter(PlatformSellers.seller_id == seller_id,
                                                            PlatformSellers.is_default.is_(True)).first()
        if not owner_platform:
            return seller_id
        owner_seller = conn.query(PlatformSellers).filter(PlatformSellers.platform_id == owner_platform.platform_id,
                                                          PlatformSellers.is_owner.is_(True)).first()
        if not owner_seller:
            return seller_id
        return owner_seller.seller_id
    except Exception as e:
        _logger.error('error when get seller')
        _logger.exception(e)
        raise e


def get_platform_owner(platform_id: int) -> int:
    owner_seller = PlatformSellers.query.filter(PlatformSellers.platform_id == platform_id,
                                                PlatformSellers.is_owner.is_(True)).first()
    if owner_seller:
        return owner_seller.seller_id


def create_or_update(data):
    seller_id = data.get('id')
    seller = get_seller(seller_id)

    if seller is not None:
        message = 'Cập nhật seller thành công'
    else:
        seller = Seller()
        seller.id = data.get('id')
        message = 'Tạo mới seller thành công'

    # Save to db
    seller.code = data.get('code')
    seller.name = data.get('name')
    seller.manual_sku = not data.get('is_auto_generated_sku')
    seller.is_manage_price = not data.get('using_goods_management_modules')
    seller.status = data.get('is_active')
    seller.address = data.get('full_address')
    seller.enterprise_code = data.get('brc_code')
    seller.slogan = data.get('slogan')
    seller.tax_number = data.get('tax_id_number')
    seller.display_name = data.get('display_name')

    db.session.add(seller)
    db.session.commit()

    return seller_id, message


def get_seller(seller_id):
    seller = Seller.query.filter(
        Seller.id == seller_id
    ).first()

    return seller


def _assign_selling_seller(seller_id, platform_id, owner_seller_id, is_default):
    platform_seller = PlatformSellers.query.filter(PlatformSellers.seller_id == seller_id,
                                                   PlatformSellers.platform_id == platform_id).first()
    if platform_seller:
        platform_seller.is_default = False
        if is_default:
            platform_seller.is_default = True
        if platform_seller.seller_id == owner_seller_id:
            platform_seller.is_owner = True
    else:
        platform_seller = PlatformSellers()
        platform_seller.seller_id = seller_id
        platform_seller.platform_id = platform_id
        platform_seller.is_default = False
        if is_default:
            platform_seller.is_default = True
        if platform_seller.seller_id == owner_seller_id:
            platform_seller.is_owner = True
        db.session.add(platform_seller)
    return platform_seller


def __assign_owner_seller(platform_id, owner_seller_id):
    owner_seller = PlatformSellers.query.filter(PlatformSellers.seller_id == owner_seller_id,
                                                PlatformSellers.platform_id == platform_id).first()
    if owner_seller:
        owner_seller.is_owner = True
    else:
        owner_seller = PlatformSellers()
        owner_seller.seller_id = owner_seller_id
        owner_seller.platform_id = platform_id
        owner_seller.is_owner = True
        db.session.add(owner_seller)


def assign_new_selling_platform(seller_id, platform_id, owner_seller_id, is_default):
    platform_seller = _assign_selling_seller(seller_id, platform_id, owner_seller_id, is_default)
    if platform_seller.seller_id != owner_seller_id:
        __assign_owner_seller(platform_id, owner_seller_id)
    db.session.commit()
    if is_default:
        data = {
            'seller_id': seller_id,
            'owner_seller_id': owner_seller_id,
            'platform_id': platform_id
        }
        platform_seller_upsert_created_signal.send(data)


def get_platform_by_seller_id(seller_id):
    seller_owners = PlatformSellers.query.filter(
        PlatformSellers.seller_id == seller_id,
        PlatformSellers.is_owner.is_(True)
    ).all()
    return [platformSeller.platform_id for platformSeller in seller_owners]


def get_seller_default_on_platform(platform_ids):
    platform_sellers = PlatformSellers.query.filter(
        PlatformSellers.platform_id.in_(platform_ids)
    ).filter(
        PlatformSellers.is_default == 1
    ).all()
    return [platformSeller.seller_id for platformSeller in platform_sellers]
