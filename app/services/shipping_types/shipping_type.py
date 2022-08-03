# coding=utf-8
import funcy
from flask_login import current_user

from catalog import models as m
from .query import ShippingTypeQuery
from ...extensions.exceptions import BadRequestException
from ...utils.sql_utils import SqlUtils
from ...utils.validation_utils import validate_required

main_table = 'shipping_types'


def get_shipping_type_list(filters, sort_field, sort_order, page, page_size):
    """get_shipping_type_list

    :param filters:
    :param sort_field:
    :param sort_order:
    :param page:
    :param page_size:
    """
    query = ShippingTypeQuery()
    query.apply_filters(filters)
    total_records = len(query)
    query.sort(sort_field, sort_order)
    query.pagination(page, page_size)
    return query.all(), total_records


def validate_duplicate_name(name):
    SqlUtils.validate_duplicate_field(m.ShippingType,
                                      m.ShippingType.name, name, f'Tên của Loại hình vận chuyển đã tồn tại')


def validate_duplicate_code(code):
    SqlUtils.validate_duplicate_field(m.ShippingType,
                                      m.ShippingType.code, code, f'Mã của Loại hình vận chuyển đã tồn tại')


def create_shipping_type(data):
    """
    Detail at:
    https://confluence.teko.vn/display/EP/Create+a+Shipping+Type
    :param data:
    :return:
    """

    name = data.get('name')
    code = data.get('code')
    validate_duplicate_name(name)
    validate_duplicate_code(code)

    entity = m.ShippingType()
    entity.name = name
    entity.code = code
    entity.is_active = True
    entity.created_by = current_user.email
    entity.updated_by = current_user.email

    m.db.session.add(entity)
    m.db.session.commit()

    return entity


def update_shipping_type(data):
    """
    Detail at:
    https://confluence.teko.vn/display/EP/Update+a+Shipping+Type
    :param data:
    :return:
    """

    entity = m.ShippingType.query.get(data.get('id'))
    validate_required(entity, f'Không tồn tại bản ghi có id = {id} trong bảng shipping_type')

    name = data.get('name')
    if entity.name.lower() != name.lower():
        validate_duplicate_name(name)

    entity.name = name
    entity.updated_by = current_user.email

    m.db.session.commit()

    return entity


def get_shipping_type_id_by_list_name(names: str):
    names = [name.strip() for name in names.split(',')]

    shipping_types = m.ShippingType.query.filter(
        m.ShippingType.name.in_(names),
        m.ShippingType.is_active == 1
    ).all()
    l_names = funcy.lpluck_attr('name', shipping_types)
    if len(names) != len(shipping_types):
        for name in names:
            if name not in l_names:
                raise BadRequestException(f'Loại hình vận chuyển "{name}" không tồn tại hoặc đã bị vô hiệu.')
    return funcy.lpluck_attr('id', shipping_types)


def get_shipping_type_by_category_id(category_id: int):
    """
    """
    category_shipping_types = m.CategoryShippingType.query.filter(
        m.CategoryShippingType.category_id == category_id
    ).all()
    return funcy.lpluck_attr('shipping_type_id', category_shipping_types)


def get_default_shipping_type():
    return m.ShippingType.query.filter(m.ShippingType.is_active,
                                       m.ShippingType.is_default).first()
