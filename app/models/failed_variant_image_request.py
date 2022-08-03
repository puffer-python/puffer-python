# coding=utf-8
from catalog.models import db
from catalog import models as m


class FailedVariantImageRequest(db.Model, m.TimestampMixin):
    __tablename__ = 'failed_variant_image_request'

    request_id = db.Column(db.String(40))
    status = db.Column(db.SmallInteger())  # 0: waiting_for_re_processing | 1: success | 2: failed
