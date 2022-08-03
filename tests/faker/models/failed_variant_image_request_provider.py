# coding=utf-8
import logging

import faker.providers

from catalog import models as m
from tests.faker import fake


class FailedVariantImageRequestProvider(faker.providers.BaseProvider):
    def failed_variant_image_request(self, request_ids=None, status=False):
        if not request_ids:
            request_ids = [fake.text() for _ in range(10)]

        failed_variant_image_requests = []

        for request_id in request_ids:
            variant_image_request_id = m.FailedVariantImageRequest()
            variant_image_request_id.request_id = request_id
            variant_image_request_id.status = status

            failed_variant_image_requests.append(variant_image_request_id)
            m.db.session.add(variant_image_request_id)
            m.db.session.flush()

        return failed_variant_image_requests
