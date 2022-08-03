# coding=utf-8
import logging
import contextlib

from tests.conftest import login_patcher

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


@contextlib.contextmanager
def logged_in_user(user):
    """ Patch the flask_login.utils._load_user function to
    return a logged in user

    :param user: the logged in user
    :return:
    """
    patcher = login_patcher(user)

    with patcher:
        yield

