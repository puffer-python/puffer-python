# coding=utf-8

from catalog.extensions import exceptions as exc
from catalog import models as m
from . import Validator


class UpdateSrmStatusValidator(Validator):
    @staticmethod
    def validate_data(sellable_id, code, **kwargs):
        if code:
            sellable = m.SellableProduct.query.get(sellable_id)
            if not sellable:
                raise exc.BadRequestException('Sản phẩm không tồn tại')
            srm_status = m.SRMStatus.query.filter(
                m.SRMStatus.code == code
            ).first()
            if not srm_status:
                raise exc.BadRequestException('Trạng thái không tồn tại hoặc chưa đồng bộ với SRM')
