# coding=utf-8
import logging
import celery as _celery
from flask import ctx, request

__author__ = 'Kien.HT'

from catalog.utils import DictToObject

_logger = logging.getLogger(__name__)


class CeleryUser:
    def __init__(self, user):
        if isinstance(user, dict):
            user = DictToObject(**user)
        self.user = user

    def user(self):
        return self.user


def make_celery(app):
    """
    Create celery application from Flask application

    :param  app:
    :return: celery.Celery
    """

    old_delay = _celery.Task.delay

    def delay(self, *args, **kwargs):
        from flask_login import current_user

        if kwargs.get('required_login') and not kwargs.get('_rq_ctx_user_email'):
            if current_user:
                kwargs['_rq_ctx_user_email'] = current_user.email

        if kwargs.get('send_environ'):
            environ = {}
            if ctx.has_request_context():
                for k, v in request.environ.items():
                    if isinstance(v, (bytes, str, int, float)):
                        environ[k] = v
            kwargs['environ'] = environ
            del kwargs['send_environ']

        old_delay(self, *args, **kwargs)

    _celery.Task.delay = delay

    celery = _celery.Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    if not celery.conf.task_always_eager:
        TaskBase = celery.Task

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return TaskBase.__call__(self, *args, **kwargs)

        celery.Task = ContextTask
    # celery.conf.task_always_eager = True
    return celery
