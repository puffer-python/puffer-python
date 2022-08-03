# coding=utf-8
import json
import logging
from sqlalchemy import (
    and_,
    exists,
)
from catalog.extensions import signals
from catalog import (
    models as m,
    biz,
)

_logger = logging.getLogger(__name__)


@biz.on_teko_msg('product.status.update')
def on_product_status_update(rk, body, properties):
    """
    Được gọi khi SRM cập nhật thông tin trạng thái sản phẩm.

    1. update thông tin trạng thái sản phẩm trong bảng products ứng với sku
    trả về từ msg.
    2. Kích hoạt luồng bắn thông tin sản phẩm sang PL nếu sản phẩm đó
    đã có trên PL.

    :param rk:
    :param body:
    :param properties:
    :return:
    """
    sku = body['product_code']
    product = m.SellableProduct.query.filter(
        m.SellableProduct.sku == sku
    ).first()  # type: m.SellableProduct

    if product:
        status = m.SellingStatus.query.join(
            m.SRMStatus,
            and_(
                m.SellingStatus.code == m.SRMStatus.selling_status,
                m.SRMStatus.code == body['status_code']
            )
        ).first()  # type: m.SellingStatus
        if status is not None:
            _logger.info('Change product status from {} to {}'.format(
                product.selling_status, status.code
            ))

            product.selling_status_code = status.code
            product.updated_by = body.get('last_update_by', 'system')
            m.db.session.commit()
            # push new data to PL
            if existed_on_pl(sku):
                signals.sellable_update_signal.send(product)


def existed_on_pl(sku):
    """

    :param sku:
    :return:
    """
    return m.db.session.query(
        exists().where(m.ProductDetail.sku == sku)
    ).scalar()
