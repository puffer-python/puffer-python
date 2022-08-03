import logging
import json

from flask import request

from catalog import models

_logger = logging.getLogger(__name__)


def log_request(func):
    def wrapper(*args, **kwargs):
        response = func(*args, **kwargs)

        try:
            request_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            request_host = request.host.split(':', 1)[0]
            request_params = getattr(request, 'args', None)
            request_body = request.get_json()
            request_user_id = request.headers.get('X-USER-ID')
            request_logs = models.RequestLog(
                request_ip=request_ip,
                request_host=request_host,
                request_method=request.method,
                request_path=request.path,
            )
            if isinstance(response, dict):
                request_logs.response_body = json.dumps(response, ensure_ascii=False)
            if request_body:
                request_logs.request_body = json.dumps(request_body, ensure_ascii=False)

            request_logs.request_params = json.dumps(
                {
                    'params': request_params,
                    'headers': dict(request.headers)
                },
                ensure_ascii=False)
            if request_user_id:
                request_logs.created_by = request_user_id
            models.db.session.add(request_logs)
            models.db.session.commit()
        except Exception as e:
            _logger.error('error when insert request log')
            _logger.exception(e)

        return response

    return wrapper
