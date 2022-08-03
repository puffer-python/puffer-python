# coding=utf-8
import logging
import marshmallow as mm

from catalog import utils
from catalog.extensions import exceptions as exc

__logger__ = logging.getLogger(__name__)
__author__ = 'Thanh.NK'


class Schema(mm.Schema):
    def __init__(self, allow_none=True, do_strip=True, **kwargs):
        super().__init__(**kwargs)
        self.allow_none = allow_none
        self.do_strip = do_strip

    @mm.pre_load
    def strip_str(self, data, **kwargs):
        if not self.do_strip:
            return data

        if not isinstance(data, dict):
            return

        data = {k: v for k, v in data.items()}
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = value.strip()

        return data

    @mm.pre_load
    def check_null_value(self, data, **kwargs):
        if not self.allow_none and data:
            for key, value in data.items():
                if value is None or value == [] or value == {}:
                    raise mm.ValidationError({
                        key: f'Assign {value} to field value is not permitted'
                    })

        return data

    def on_bind_field(self, field_name, field_obj):
        """

        :param field_name:
        :param field_obj:
        :return:
        """
        field_obj.data_key = utils.camel_case(field_obj.data_key or field_name)

    def load_include_all(self, data):
        try:
            super().load(super().dump(data), unknown=mm.INCLUDE)
        except mm.ValidationError as e:
            raise exc.BadRequestException(
                errors=format_errors(e)
            )


def format_errors(error):
    """Format marshmallow errors to rest_plus errors
    :param error: dict
    :return: dict
    errors:
    {
        "page_size": ["Missing data"],
        "page": ["Missing data"]
    }
    """
    return [{'field': field, 'message': message}
            for field, message in error.messages.items()]
