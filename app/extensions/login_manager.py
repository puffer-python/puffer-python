# coding=utf-8
import json
import traceback
import logging
import flask
import flask_login
import requests
from flask import current_app

import config
from catalog import models as m
from catalog.extensions import exceptions as exc

__author__ = 'Kien.HT'

_logger = logging.getLogger(__name__)

authorization_header = 'Authorization'
PREFIX = 'Bearer '

login_manager = flask_login.LoginManager()


def init_app(app, **kwargs):
    """
    Extension initialization point
    :param app:
    :param kwargs:
    :return:
    """
    login_manager.init_app(app)


def safe_convert_int(value):
    """
    Safely convert string value to int. Return None if not convertible.
    :param value:
    :return:
    """
    try:
        return int(value)
    except (ValueError, TypeError, AttributeError):
        return None


class User(object):
    """Provide User object for LoginManager class"""

    def __init__(self, access_token, user_info, seller_id):
        """
        :param access_token:
        :param user_info:
        """
        self.is_authenticated = True
        self.is_active = True
        self.access_token = access_token
        self.email = user_info.email
        self.seller_id = safe_convert_int(seller_id)

        seller_ids = user_info.seller_ids
        if seller_ids is not None:
            self.seller_ids = [int(x) for x in str(seller_ids).split(',')]
        else:
            self.seller_ids = []

    @property
    def is_admin(self):
        return self.seller_ids == [0]

    def get_id(self):
        return self.access_token


class InternalUser:
    def __init__(self, email, seller_id):
        self.is_authenticated = True
        self.is_active = True
        self.email = email
        self.seller_id = safe_convert_int(seller_id)

        # TODO: this isn't best solution, need improvement
        self.seller_ids = [self.seller_id]

    def get_id(self):
        return self.email


@login_manager.request_loader
def load_user_from_request(request):
    """
    Load authenticated user from request
    :param request:
    :return:
    """
    user_id = request.headers.get('X-USER-ID')
    current_seller_id = request.headers.get('X-SELLER-ID')
    token = request.headers.get(authorization_header)
    _logger.info(f'api {request.path} has headers X-USER-ID: {user_id} X-SELLER-ID: {current_seller_id} Token: {token}')
    try:
        # TODO: use environ for fake flask context in celery worker
        if (not user_id or not token) and hasattr(flask, 'request'):
            if flask.request.host in current_app.config['INTERNAL_HOST_URLS']:
                # basically, just return a user with essential info such as email and seller_id.
                return InternalUser(
                    email=request.headers.get('X-USER-EMAIL'),
                    seller_id=current_seller_id
                )
            raise exc.UnAuthorizedException()
        user = m.IAMUser.query.filter(m.IAMUser.iam_id == user_id).first()
        if user and user.access_token == token:
            if not user.check_and_update_seller_id(current_seller_id):
                return None
            return User(token, user, current_seller_id)

        user_info = get_user_from_api(token)
        if user:
            update_user_info_if_needed(user, user_info, token)
        else:
            user = add_user_for_first_time_login(user_id, user_info, token)
        if not user.check_and_update_seller_id(current_seller_id):
            return None
        return User(token, user, current_seller_id)
    except Exception as e:
        from catalog.utils.slack import slack_alert
        try:
            request_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            request_host = request.host.split(':', 1)[0]
            request_token = token or 'no token'
            err_info = repr(e)
            log_info = traceback.format_exc()
            request_body = {"token": request_token}
            response_body = {'error': err_info, 'log': log_info}

            request_log = m.RequestLog(
                request_ip=request_ip,
                request_host=request_host,
                request_method=request.method,
                request_path=request.path,
                request_params='login_manager_error',
                request_body=json.dumps(request_body),
                response_body=json.dumps(response_body)
            )
            m.db.session.add(request_log)
            m.db.session.commit()
            log_content = f'Api {request.method} `{request.path}` has error with token `{token}` and request log id `{request_log.id}`'
            _logger.error(log_content)
            slack_alert.delay(title='Login manager exception', content=log_content)
        except:
            pass
        raise e


def get_user_from_api(token):
    """

    :param token:
    :return:
    """
    res = requests.get(
        url=flask.current_app.config['USER_API_V2'],
        headers={authorization_header: token}
    )
    if res.status_code != 200:
        raise exc.UnAuthorizedException()
    return res.json()


def update_user_info_if_needed(user, user_info, token):
    """

    :param user:
    :param user_info:
    :param token:
    :return:
    """
    user.access_token = token

    email = user_info.get('email')
    if user.email != email:
        user.email = email

    name = user_info.get('name')
    if user.name != name:
        user.name = name

    meta_data = user_info.get('meta_data')
    if meta_data:
        seller_ids = meta_data.get('seller_id')
        if seller_ids and user.seller_ids != seller_ids:
            user.seller_ids = seller_ids
    else:
        if user.seller_ids:
            user.seller_ids = None

    m.db.session.commit()


def add_user_for_first_time_login(user_id, user_info, token):
    """

    :param user_id:
    :param user_info:
    :param token:
    :return:
    """
    user = m.IAMUser()
    user.iam_id = user_id
    user.access_token = token
    user.email = user_info.get('email')
    user.name = user_info.get('name')
    meta_data = user_info.get('meta_data')
    if meta_data:
        user.seller_ids = meta_data.get('seller_id')
    m.db.session.add(user)
    m.db.session.commit()

    return user
