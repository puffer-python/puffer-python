# coding=utf-8
import logging
import enum
import faker.providers

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class SRMRequestProvider(faker.providers.BaseProvider):
    def product_status_update_msg(self, product_code, status_code=None):
        return {
            "product_code": product_code,
            "status_name": "Bình thường",
            "last_updated_on": "2019-07-04 03:55:31",
            "__ts": "2019-07-04 03:55:32.259324",
            "status_code": status_code or "0",
            "last_updated_by": "kien.ht@teko.vn",
            "status_description": "Hàng kinh doanh bình thường",
            "__sign": "2e55a688ddcac16e952534adf36e70724fcf590f"
        }
