# coding=utf-8
import logging

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


def wrap_response(message="", data=None, exc=None):
    """
    Return general HTTP response
    :param message:
    :param data:
    :param exc:
    :return:
    """
    return wrap_errors(exc) if exc else {
        'code': 'SUCCESS',
        'message': message,
        'result': data,
    }


def wrap_errors(exc):
    """
    :param exc.HTTPException exc:
    :return:
    """
    return {
        "code": exc.code,
        "message": str(exc),
        "result": exc.errors,
    }, exc.http_code
