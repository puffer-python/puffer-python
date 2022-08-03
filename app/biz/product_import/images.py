import logging
import uuid
from copy import deepcopy

import requests
from urllib import parse
from flask_login import current_user

import config

from flask import _request_ctx_stack
from catalog import celery, models, app
from catalog.extensions import signals
from catalog.extensions.celery import CeleryUser
from catalog.extensions.exceptions import BadRequestException
from catalog.services.products import ProductVariantService
from catalog.services.products.variant import delete_images, update_image
from catalog.validators.variant import UpdateVariantValidator

_logger = logging.getLogger(__name__)

DEFAULT_PROCESSING_MESSAGE = "Đang xử lý"
DEFAULT_SUCCESS_MESSAGE = "Thành công"
DEFAULT_MAXIMUM_CREATABLE_MESSAGE = "Hệ thống chỉ cho phép tối đa {} ảnh mỗi biến thể"
DEFAULT_EXCEPTION_MESSAGE = "Hệ thống gặp lỗi"

DEFAULT_MAXIMUM_CREATABLE_IMAGE = 36

GOOGLE_DRIVE_DOMAIN = 'drive.google.com'
GOOGLE_DRIVE_FILE_DOWNLOAD_URL = 'https://drive.google.com/uc?id={}&export=download'


@signals.on_create_variant_images
def on_create_variant_images(params):
    """
    Create variant images asynchronously
    """
    import_variant_images.delay(
        variant_id=params.get('variant').get('id'),
        urls=params.get('variant').get('images'),
        request_id=params.get('request_id'),
        email=params.get('email'),
        send_environ=True
    )


@celery.task(
    queue='import_variant_images'
)
def import_variant_images(
        variant_id, urls, email, request_id=None, environ=None,
        max_creatable_image=DEFAULT_MAXIMUM_CREATABLE_IMAGE):
    """
    request_id: if request_id is None, the result is not logged
    """

    with app.request_context(environ):
        # Init the status of creating images
        if isinstance(urls, str):
            urls = urls.split('\n')
        data = {
            'variants': [{
                'id': variant_id,
                'images': []
            }]
        }

        variant_image_logs = urls
        if request_id:
            variant_image_logs = get_old_variant_image_log(request_id)
            if len(variant_image_logs) == 0:
                variant_image_logs = create_variant_image_log(variant_id, urls, request_id)

        # Start creating the images
        total_success_urls = 0
        valid_urls = []

        try:
            user = {
                'email': email
            }
            _request_ctx_stack.push(CeleryUser(deepcopy(user)))

            for item in variant_image_logs:
                url = item.input_url if request_id else item
                try:
                    if total_success_urls == max_creatable_image:
                        if request_id:
                            item.result = DEFAULT_MAXIMUM_CREATABLE_MESSAGE.format(max_creatable_image)
                        continue

                    data['variants'][0]['images'] = [{
                        'url': url
                    }]
                    response = UpdateVariantValidator.validate_image(
                        data=data,
                        allow_all_urls=True,
                        verify=False
                    )[0]

                    success_url = url if url.startswith(config.BASE_IMAGE_URL) else upload_to_the_cloud(
                        response).json().get('image_url')
                    valid_urls.append({
                        'url': success_url
                    })

                    total_success_urls += 1

                    if request_id:
                        item.result = DEFAULT_SUCCESS_MESSAGE
                        item.success_url = success_url

                except BadRequestException as error:
                    if request_id:
                        item.result = error.message

            # Replace new records to database
            data['variants'][0]['images'] = valid_urls
            delete_images(data, auto_commit=False)
            update_image(variant_id=variant_id, image_data=valid_urls, auto_commit=True)

            # Log the final result
            if request_id:
                if len(urls) == 0:
                    variant_image_log = models.VariantImageLog(
                        variant_id=variant_id,
                        input_url=None,
                        result=DEFAULT_SUCCESS_MESSAGE,
                        request_id=request_id
                    )
                    models.db.session.add(variant_image_log)
                sku = models.SellableProduct.query.filter(models.SellableProduct.variant_id == variant_id).first()
                if sku:
                    sku.updated_by = email
            models.db.session.commit()
        except Exception as e:
            _logger.exception(e)
            for item in variant_image_logs:
                item.result = DEFAULT_EXCEPTION_MESSAGE
            models.db.session.commit()


def upload_to_the_cloud(response):
    try:
        content_type = response.headers.get('Content-Type')

        send_file = {'file': (
            '{}.{}'.format(uuid.uuid4(), content_type.replace('image/', '')),
            response.content,
            content_type
        )}

        response = requests.post('{}/upload/image?cloud=true'.format(config.FILE_API), files=send_file)

        if response.status_code != 200:
            raise BadRequestException('Hệ thống đang gặp lỗi. Vui lòng thử lại sau')

        return response
    except requests.exceptions.RequestException:
        raise BadRequestException('Hệ thống đang gặp lỗi. Vui lòng thử lại sau')


def get_old_variant_image_log(request_id):
    """
    Need to get old logs because variant_image_log can be duplicated by re-updating by flask.cli.command
    """
    logs = models.db.session.query(models.VariantImageLog).filter(
        models.VariantImageLog.request_id == request_id
    ).all()
    return logs


def create_variant_image_log(variant_id, urls, request_id, message=DEFAULT_PROCESSING_MESSAGE):
    variant_image_logs = []

    for i in range(len(urls)):
        url = urls[i].strip()
        if not url:
            continue
        variant_image_log = models.VariantImageLog(
            variant_id=variant_id,
            input_url=url,
            result=message,
            request_id=request_id
        )

        variant_image_logs.append(variant_image_log)
        models.db.session.add(variant_image_log)
    models.db.session.commit()
    return variant_image_logs


def download_from_internet_and_upload_to_the_cloud(url, **kwargs):
    try:
        _DEFAULT_MAX_IMAGE_SIZE = 2 * 1024 * 1024
        if url.startswith(config.BASE_IMAGE_URL):
            return url
        response = download_from_internet(url, verify=kwargs.get('verify', True))
        if response.status_code != 200:
            raise BadRequestException(f'Không tải được link ảnh: {url}')
        if not response.headers.get('Content-Type') in ['image/jpeg', 'image/png']:
            raise BadRequestException(f'Ảnh lấy theo {url} không đúng định dạng')
        if int(response.headers.get('Content-Length')) > _DEFAULT_MAX_IMAGE_SIZE:
            raise BadRequestException(f'Ảnh lấy theo {url} đang vượt quá 2MB')
    except Exception:
        raise BadRequestException(f'Không tải được link ảnh: {url}')
    return upload_to_the_cloud(response).json().get('image_url')


def download_from_internet(url, verify):
    if GOOGLE_DRIVE_DOMAIN in url:
        try:
            url_parse = url.split('/')
            file_id = url_parse.pop(5)
        except IndexError:
            url_parse = parse.urlsplit(url)
            file_id = dict(parse.parse_qs(url_parse.query)).get('id')
        if isinstance(file_id, list):
            file_id = file_id[0]
        drive_download_url = GOOGLE_DRIVE_FILE_DOWNLOAD_URL.format(file_id)
        response = requests.get(drive_download_url, verify=verify)
        return response
    else:
        response = requests.get(url, verify=verify)
        return response
