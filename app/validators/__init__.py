# coding=utf-8
import logging

from catalog.extensions import exceptions as exc

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


class Validator(object):
    @classmethod
    def validate(cls, data, obj_id=None, **kwargs):
        """

        :param data:
        :param obj_id:
        :return:
        """

        # dynamically get all validators
        validators = [
            getattr(cls, fn)
            for fn in dir(cls)
            if (
                callable(getattr(cls, fn)) and
                fn.startswith('validate_')
            )
        ]
        for validator in validators:
            validator(**data, obj_id=obj_id, **kwargs)

        return data
