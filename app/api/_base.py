# coding=utf-8

from marshmallow import fields as origin_fields
from marshmallow import (
    validate,
    post_load,
)

from catalog.extensions.marshmallow import (
    Schema,
    fields,
)


class ListParamBase(Schema):
    page = origin_fields.Integer(validate=(
        validate.Range(min=1, max=1000000000)
    ), missing=1)
    page_size = origin_fields.Integer(validate=(
        validate.Range(min=1, max=1000000000)
    ), missing=10)


class SortableParam(Schema):
    order_by = origin_fields.String()

    @post_load
    def unpack_sort_param(self, data, **kwargs):
        value = data.get('order_by')
        data.update({
            'sort_field': None,
            'sort_order': 'ascend'
        })
        if not value:
            return data
        data['sort_field'] = value
        if value.startswith('-'):
            data['sort_order'] = 'descend'
            data['sort_field'] = value[1:]
        return data


class ListResponseBase(Schema):
    current_page = fields.Integer()
    page_size = fields.Integer()
    total_records = fields.Integer()


def extract_hyper_param_from_list_request(args):
    """extract_hyper_param_from_list_request

    :param args:
    """
    meta = dict(
        page=args.pop('page', 0),
        page_size=args.pop('page_size', 10),
        sort_order=args.pop('sort_order', 'asc'),
        sort_field=args.pop('sort_field', None),
    )
    return meta, args


def make_pagination_response(page, page_size, total_records, result):
    """make_pagination_response

    :param page:
    :param page_size:
    :param total_records:
    :param result:
    """
    return {
        'current_page': page,
        'page_size': page_size,
        'total_records': total_records,
        'result': result
    }
