# coding=utf-8
# pylint: disable=E0102
import decimal
import re
from typing import Callable

import marshmallow

from marshmallow import fields
from marshmallow.validate import ValidationError

from . import validators

__author__ = 'Kien.HT'


def check_none(value):
    """

    :param value:
    :return:
    """
    null_value = ('null', 'None')
    if value in null_value:
        return None
    return value


class Number(fields.Number):
    pass


class Raw(fields.Raw):
    pass


class Field(fields.Field):
    pass


class Date(fields.Date):
    pass


class DateTime(fields.DateTime):
    pass


class Float(fields.Float):
    pass


class List(fields.List):
    pass


class Nested(fields.Nested):
    pass


class String(fields.String):
    def __init__(self, min_len=None, max_len=None, match=None, **kwargs):
        """

        :param maxlength:
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.min_len = min or 0
        self.max_len = max or 255
        self.match = match

        self.validators.append(validators.Length(min=min_len, max=max_len))

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if self.match and not re.search(self.match, value):
            raise ValidationError({
                attr: f'{value} chỉ gồm ký tự chữ và số viết liền'
            })
        return value


class Integer(fields.Integer):
    def __init__(self, min_val=0, max_val=2147483647, strict=True,
                 restricted_values=None, *args, **kwargs):
        """

        :param int min_val:
        :param int max_val:
        :param strict:
        :param restricted_values:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.strict = strict
        self.validators.append(
            validators.Any(
                validators.Range(min=min_val, max=max_val),
                validators.IsNone()
            )
        )
        self.restricted_values = restricted_values

    def _validated(self, value):
        value = super()._validated(value)
        if self.restricted_values and value not in self.restricted_values:
            raise ValidationError(
                f'{value} is not a valid value'
            )
        return value


class NotNegativeFloat(fields.Float):
    def __init__(self, min_val=None, max_val=None, **kwargs):
        """

        :param min_val:
        :param max_val:
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.min = min_val or 0.0
        self.validators.append(
            validators.Any(
                validators.IsNone(),
                validators.Range(min=min_val, max=max_val)
            )
        )

    def _format_num(self, value):
        value = check_none(value)

        return super()._format_num(value)


class PositiveFloat(fields.Float):
    def __init__(self, min_val=None, max_val=None, **kwargs):
        """

        :param min_val:
        :param max_val:
        :param kwargs:
        """
        super().__init__(**kwargs)
        self.min = min_val or 0.0
        self.validators.append(
            validators.Any(
                validators.IsNone(),
                validators.Range(min=min_val, max=max_val)
            )
        )

    def _validated(self, value):
        value = super()._validated(value)
        if value <= 0.0:
            raise ValidationError(
                f'{value} is not a positive value.'
            )
        return value


class MoneyAmount(Integer):
    num_type = decimal.Decimal

    def __init__(self, as_string=False, **kwargs):
        """

        :param as_string:
        :param kwargs:
        """
        super().__init__(as_string, **kwargs)
        self.validators.insert(0, validators.Range(min=0))

    def _deserialize(self, value, attr, data):
        value = check_none(value)
        return int(value) if value is not None else None


class StringList(marshmallow.fields.String):
    def __init__(
        self,
        cast_fn: Callable = str,
        ignore_cast_error: bool = False,
        min_len: int = 0,
        *args,
        **kwargs
    ):
        self.min_len = min_len
        self.cast_fn = cast_fn
        self.ignore_cast_error = ignore_cast_error
        super().__init__(*args, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs):
        value = super()._deserialize(value, attr, data, **kwargs)
        if len(value) < self.min_len:
            raise ValidationError(f'Shorter than minimum length {self.min_len}.')
        if value is marshmallow.missing:
            return
        if not value:
            return []

        STRING_LIST_FMT = r'^[^,]*([^,]{1,},{1})*[^,]+$'
        if not re.fullmatch(STRING_LIST_FMT, value):
            raise ValidationError(f'`{value}` is not string list format')

        ret = list()
        for ch in value.split(','):
            if ch:
                try:
                    v = self.cast_fn(ch)
                except ValueError:
                    if not self.ignore_cast_error:
                        raise ValidationError(f'Value must be {self.cast_fn.__name__}')
                else:
                    ret.append(v)
        return ret


class Boolean(fields.Boolean):
    def __init__(self, allow_str=False, allow_num=False, **kwargs):
        super().__init__(**kwargs)
        self.truthy = {True} if not allow_str else {True, '1'}
        self.falsy = {False} if not allow_str else {False, '0'}
        self.allow_num = allow_num

    def _deserialize(self, value, attr, data, **kwargs):
        if type(value) is bool:
            return value
        if value in self.truthy:
            if isinstance(value, (int, float)):
                if self.allow_num:
                    return True
                raise ValidationError(f'{value} is not a valid bool value')
            return True
        if value in self.falsy:
            if isinstance(value, (int, float)):
                if self.allow_num:
                    return False
                raise ValidationError(f'{value} is not a valid bool value')
            return False

        raise ValidationError(f'{value} is not a valid bool value')
