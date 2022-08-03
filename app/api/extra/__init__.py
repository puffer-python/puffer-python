# coding=utf-8
from flask import g
import flask_restplus
from flask import request
from flask_login import current_user

from catalog.extensions import flask_restplus as fr
from catalog.services.extra import ExtraService
from . import schema
from catalog.extensions.flask_cache import cache

extra_ns = fr.Namespace(
    name='extra',
    path='/extra'
)


@extra_ns.route('', methods=['GET'])
class Extra(fr.Resource):
    """
    Trả về extra data cho phía client.
    """
    @cache.cached(timeout=1800, query_string=True)
    @extra_ns.expect(schema_cls=schema.ExtraDataRequest, location='args')
    @extra_ns.marshal_with(schema.Extra)
    def get(self):
        """
        Trả về danh sách các thông tin liên quan của sản phẩm.
        :return:
        """
        service = ExtraService.get_instance()
        return service.get_extra_info(g.args)


old_extra_ns = flask_restplus.Namespace(
    name='old extra',
    path='/extra-data'
)


@old_extra_ns.route('', methods=['GET'])
class OldExtra(flask_restplus.Resource):
    """
    Trả về extra data cho client.
    """

    def get(self):
        """
        Trả về danh sách các thông tin liên quan của sản phẩm.
        :return:
        """
        return OldExtra.__get_extra(request.args, getattr(current_user, 'seller_id', None))

    @staticmethod
    @cache.memoize(timeout=1800)
    def __get_extra(args, seller_id):
        service = ExtraService.get_instance()
        extra_data = service.get_old_extra_data(args, seller_id)

        return schema.OldExtraData().dump(extra_data)
