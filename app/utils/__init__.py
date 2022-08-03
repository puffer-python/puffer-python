# coding=utf-8

import pytz
from datetime import datetime
import logging
import json
import re
import random
import string
from slugify import slugify
from flask import (
    request,
    ctx,
)
from catalog.constants import COLOR_ERROR_IMPORT

__author__ = 'Kien.HT'


_logger = logging.getLogger(__name__)


def highlight_error(x):
    return [f'background-color: {COLOR_ERROR_IMPORT}' if x['Kết quả'] != 'Thành công' else ''
            for v in x]


def get_or_create(session, model, **kwargs):
    """
    Get an instance of sqlalchemy model, or create a new one if not
    existed yet.

    :param session:
    :param model:
    :param kwargs:
    :return:
    """
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model()
        for k, v in kwargs.items():
            setattr(instance, k, v)
        session.add(instance)

        return instance


def process_validation_errors(errors):
    """
    :param errors:
    :return:
    """
    res = {}
    for k, v in errors.items():
        if k == 'data':
            return process_validation_errors(v)
        elif k == 'attributes':
            res.update({
                'field': 'attributes',
                'message': 'Dữ liệu attribute không hợp lệ'
            })
        elif k == 'seo_info':
            res.update({
                'field': 'seo_info',
                'message': 'Thông tin SEO chưa hợp lệ'
            })
        else:
            if k == '_schema':
                return v[0]
            elif isinstance(v, list):
                res.update({
                    'field': k,
                    'message': v[0]
                })
            else:
                for kk, kv in v.items():
                    res.update({
                        'field': kk,
                        'message': kv
                    })

    return res


patterns = {
    '[àáảãạăắằẵặẳâầấậẫẩ]': 'a',
    '[đ]': 'd',
    '[èéẻẽẹêềếểễệ]': 'e',
    '[ìíỉĩị]': 'i',
    '[òóỏõọôồốổỗộơờớởỡợ]': 'o',
    '[ùúủũụưừứửữự]': 'u',
    '[ỳýỷỹỵ]': 'y'
}


def convert(text):
    """
    Convert from 'Tieng Viet co dau' thanh 'Tieng Viet khong dau'
    text: input string to be converted
    Return: string converted
    """
    output = text
    for regex, replace in patterns.items():
        output = re.sub(regex, replace, output)
        # deal with upper case
        output = re.sub(regex.upper(), replace.upper(), output)
    return output


def remove_accents(text):
    """
    Convert from 'Tieng Viet co dau' thanh 'Tieng Viet khong dau' using unidecode lib.
    It can process well with multiple percussion
    text: input string to be converted
    Return: string converted
    """
    import unidecode
    return unidecode.unidecode(text)


def normalized(s):
    """
    Convert and lowercase, then trim
    :param s:
    :return:
    """
    return convert(s).lower().strip() if s else None


def keep_single_spaces(s):
    """
    Convert " ABC    DEF " to "ABC DEF"
    """
    if isinstance(s, str):
        return ' '.join(s.strip().split())
    return s


def create_chunks(src, step):
    res = []
    for i in range(0, len(src), step):
        res.append(src[i:i + step])

    return res


def reformat_dict(data):
    """

    :param dict:
    :return:
    """
    if not isinstance(data, dict):
        return data
    formatted_data = {}
    for key in data:
        formatted_key = key
        if isinstance(key, (bytes, bytearray)):
            formatted_key = key.decode('utf-8')
        if isinstance(data[key], dict):
            formatted_data[formatted_key] = reformat_dict(data[key])
        elif isinstance(data[key], (bytes, bytearray)):
            formatted_data[formatted_key] = data[key].decode('utf-8')
        else:
            formatted_data[formatted_key] = data[key]
    return formatted_data


def rabbitmq_properties_to_dict(properties):
    """ Convert RabbitMQ Basic Properties to Dict
    :param pika.spec.BasicProperties properties:
    :rtype dict:
    """
    if isinstance(properties, dict):
        return reformat_dict(properties)
    return {
        'content_type': properties.content_type,
        'content_encoding': properties.content_encoding,
        'headers': properties.headers,
        'delivery_mode': properties.delivery_mode,
        'priority': properties.priority,
        'correlation_id': properties.correlation_id,
        'reply_to': properties.reply_to,
        'expiration': properties.expiration,
        'message_id': properties.message_id,
        'timestamp': properties.timestamp,
        'type': properties.type,
        'user_id': properties.user_id,
        'app_id': properties.app_id,
        'cluster_id': properties.cluster_id,
    }


def filter_active_leaf_categories(categories):
    """
    Filter only active leaf categories from a list of categories
    :param categories: list of categories want to filter
    :return:
    """

    has_child = {}  # Define a dict to check child for all categories
    for category in categories:
        if category.is_active:
            has_child[category.parent_id] = True

    return [category.name for category in categories
            if (category.is_active and not has_child.get(category.id))]


def list_has_duplicates(mylist):
    """
    Check if a list has duplicate elements
    :param mylist:
    :return:
    """
    if len(set(mylist)) != len(mylist):
        return True
    return False


def remove_duplicate_from_list(mylist):
    """
    Remove duplicates from list
    :param mylist:
    :return:
    """
    return list(dict.fromkeys(mylist))


def is_json(str_input):
    """
    Check if string input is a valid json or not
    :param str_input:
    :return:
    """
    try:
        json.loads(str_input)
    except (TypeError, ValueError):
        return False
    return True


def format_validation_error(err):
    """
    Transform marshmallow validation error output to a more friendly format.

    :param err:
    :return:
    """
    res = []
    for k, v in err.items():
        if k == '_schema':
            res = res + v
        else:
            res.append({k: v})

    return res


def random_string(length=6):
    """Generate a random string of letters and digits """
    text = string.ascii_letters + string.digits
    return ''.join(random.choice(text) for i in range(length))


def camel_case(s):
    """
    Perform string inflection
    :param str s: input string
    :return:
    """
    parts = iter(s.split("_"))
    return next(parts) + "".join(i.title() for i in parts)


def generate_url_key(string):
    return ''.join(filter(
        lambda c: re.fullmatch('[a-zA-Z0-9\-]', c),
        slugify(convert(string))
    ))


def flatten_list(l):
    """
    flatten a 2-dim list

    :param l:
    :return:
    """
    return [item for sl in l for item in sl]


def get_utc_time(local_name, fmt=None):
    timezones = pytz.country_timezones[local_name]
    if not timezones:
        raise ValueError(f'Local {local_name} not exist')
    local = pytz.timezone(timezones[0])
    now = datetime.now()
    now_dst = now.astimezone(local)
    if fmt:
        return now_dst.strftime(fmt)
    return now_dst


def contain_special_char(string):
    pass
    # chars = ('[^0-9a-zA-Z áàảãạÁÀẢÃẠâÂấẤầẦẩẨẫẪậẬăĂắẮằẰẳẲẵẴặẶđĐéÉèÈẻẺẽ'
    #          'ẼẹẸêÊếẾềỀểỂễỄệỆíÍìÌỉỈĩĨịỊóÓòÒỏỎõÕọỌôÔốỐồỒổỔỗỖộỘơƠớỚờỜởỞ'
    #          'ỡỠợỢúÚùÙủỦũŨụỤưƯứỨừỪửỬữỮựỰýÝỳỲỷỶỹỸỵỴ]()')
    # return bool(re.findall(chars, string))


def dict_diff(old_dict: dict, new_dict: dict) -> list:
    """
    return diff of 2 dicts in format: {"key1":{"old":"old_value_key1", "new":"new_value_key1"}}
    :param old_dict: dict
    :param new_dict: dict
    :return: dict
    """
    return [{k: {'old': old_dict.get(k), 'new': new_dict.get(k)}}
            for k in set(list(old_dict) + list(new_dict)) if old_dict.get(k) != new_dict.get(k)]


def decapitalize(str):
    """
    Decapitalize the first character in string. Other characters
    remain unchanged.
    Example: Decapitalize string -> decapitalize string

    :param string str:
    :return:
    """
    return str[0].lower() + str[1:]


class DictToObject:
    def __init__(self, **kwargs):
        self.__dict__.update(**kwargs)


def environ2json():
    json_types = (int, float, str, bytes)
    environ = {}
    if ctx.has_app_context():
        environ = {
            k: v for k, v in request.environ.items() if isinstance(v, json_types)
        }
    return environ


def __cast_boolean(val, default):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        val = val.lower()

    switch = {
        'true': True,
        1: True,
        '1': True,
        'false': False,
        0: False,
        '0': False,
    }
    return switch.get(val, default)


def safe_cast(val, to_type, default=None):
    try:
        if to_type == bool:
            return __cast_boolean(val, default)
        return to_type(val)
    except (ValueError, TypeError):
        return default


def cast_separated_string_to_ints(separated_str: str, sep: str = ','):
    return [int(v) for v in separated_str.split(sep) if v.isnumeric()]


def convert_to_html_tag(s):
    return s.replace("\n", "<br> ")
