# coding=utf-8
import logging
from werkzeug.exceptions import HTTPException as BaseHTTPException
from werkzeug.http import HTTP_STATUS_CODES

from catalog.models import db
from catalog.extensions.flask_restplus import response_wrapper

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class HTTPException(BaseHTTPException):
    def __init__(self, message='', errors=None, code=200, http_code=None):
        self.message = message
        self.errors = errors
        self.code = code
        self.http_code = http_code

    @property
    def name(self):
        return HTTP_STATUS_CODES.get(self.http_code, 'Unknown Error')

    def __repr__(self):
        return "%s %s: %s" % (
            self.__class__.__name__,
            self.http_code,
            self.name
        )

    def __str__(self):
        return self.message


class BadRequestException(HTTPException):
    def __init__(self, message='Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại', errors=None, code='INVALID'):
        super().__init__(message, errors, code, 400)


class NotFoundException(HTTPException):
    def __init__(self, message='Resource Not Found', errors=None, code='NOT_FOUND'):
        super().__init__(message, errors, code, 404)


class ValidateException(HTTPException):
    def __init__(self, message='Operation not permitted', errors=None, code='INVALID'):
        super().__init__(message, errors, code, 405)


class UnAuthorizedException(HTTPException):
    def __init__(self, message='Unauthorized error', errors=None, code='INVALID'):
        super().__init__(message, errors, code, 401)


class UnprocessableEntityException(HTTPException):
    def __init__(self, message='Unprocessable entity', errors=None, code='INVALID'):
        super().__init__(message, errors, code, 422)


class ServerError(HTTPException):
    def __init__(self, message='Internal server error', errors=None, code='ERROR'):
        super().__init__(message, errors, code, 500)


class InvalidDataException(Exception):  # TODO: remove
    def __init__(self, errors):
        self.errors = errors


def global_error_handler(exc):
    db.session.rollback()
    return response_wrapper.wrap_response(exc=exc)
