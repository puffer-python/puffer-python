# coding=utf-8
import functools
import logging

import click

from catalog import app, models

__author__ = 'Minh.ND'

from catalog.extensions import signals

_logger = logging.getLogger(__name__)


@app.cli.command()
@click.argument('email')
@click.argument('count')
def upload_external_images(email, count):
    """The command to upload external images base on variant_image_logs table
    Params:
        - email: the email of the user
        - count: the number of request_ids which will be handled each command calls

    Problems:
        - The celery "import_variant_images" can be failed accidentally and lose messages.

    Actions:
        - Trigger celery worker re-run the failed request_id in failed_variant_image_request
    """
    count = int(count)

    failed_variant_image_requests = [item for item in models.FailedVariantImageRequest.query.filter(
        models.FailedVariantImageRequest.status == 0
    ).limit(count)]

    for failed_variant_image_request in failed_variant_image_requests:
        # Re-create a request body
        variant_image_log = models.VariantImageLog.query.filter(
            models.VariantImageLog.request_id == failed_variant_image_request.request_id
        ).all()

        if len(variant_image_log):
            variant_id = variant_image_log[0].variant_id
            images = [log.input_url for log in variant_image_log]

            signals.create_variant_images_signal.send({
                'request_id': failed_variant_image_request.request_id,
                'variant': {
                    'id': variant_id,
                    'images': images,
                },
                'email': email
            })

        failed_variant_image_request.status = 1

    models.db.session.commit()



