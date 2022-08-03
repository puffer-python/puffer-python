# coding=utf-8
import logging

from flask import (
    request,
    g,
    Response,
)
from flask_restplus import Namespace as OriginalNamespace
from flask_restplus._http import HTTPStatus

from catalog.extensions import exceptions as exc
from catalog.extensions import marshmallow as mm

from .response_wrapper import wrap_response

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Namespace(OriginalNamespace):
    def expect(self, schema_cls, location, **kwargs):
        """wargs
        A decorator to Specify the expected input model

        :param type schema_cls:
        :param str location: args|body
        :param kwargs:
        :return:
        """
        def before_request_handle():
            assert location in ('args', 'body'), 'location must be args or body'

            if location == 'body' and request.json == {}:
                raise exc.BadRequestException(
                    'Empty payload is not permitted'
                )

            data = request.args if location == 'args' else request.json
            try:
                data = schema_cls(**kwargs).load(data)
            except mm.ValidationError as e:
                raise exc.BadRequestException(
                    errors=mm.format_errors(e)
                )
            setattr(g, location, data)

        def request_handle_wrapper(request_handle):
            """
            Before request handler
            :param request_handle:
            :return:
            """
            def request_handle_decorator(*args, **kwargs):
                before_request_handle()
                return request_handle(*args, **kwargs)
            return request_handle_decorator
        return request_handle_wrapper

    def marshal_with(self, schema_cls, as_list=False,
                     code=HTTPStatus.OK, description=None, **kwargs):
        """
        A decorator specifying the fields to use for serialization.

        :param schema_cls:
        :param bool as_list: Indicate that the return type
                            is a list (for the documentation)
        :param int code: Optionally give the expected HTTP response code
                            if its different from 200
        :param description:
        """
        def wrapper(func):
            def request_handle_decorator(*args, **kw):
                def dump_from_schema(data, as_list):
                    if not as_list or not isinstance(data, list):
                        return schema_cls(**kwargs).dump(data)
                    else:
                        result = []
                        for d in data:
                            result.append(schema_cls(**kwargs).dump(d))
                        return result
                rv = func(*args, **kw)
                if isinstance(rv, tuple):
                    data, message = rv
                    data = dump_from_schema(data=data, as_list=as_list)
                    return wrap_response(message=message, data=data)
                else:
                    if isinstance(rv, Response):
                        return rv
                    return wrap_response(data=dump_from_schema(rv, as_list))
            return request_handle_decorator
        return wrapper
