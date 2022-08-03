# coding=utf-8
import config
from flask_login import current_user
from catalog import models as m
from catalog.constants import UOM_CODE_ATTRIBUTE
from .attribute import AttributeService


def get_attributes_of_attribute_set(group_ids):
    """
    Return all attributes of an attribute set
    Thanks to attribute_set -> groups -> attributes relation, we can get
    all attributes of a set by querying all attributes of groups of this set.

    :param list[int] group_ids:
    :return:
    """
    attributes = m.Attribute.query.join(
        m.AttributeGroupAttribute
    ).filter(
        m.Attribute.id == m.AttributeGroupAttribute.attribute_id,
        m.AttributeGroupAttribute.attribute_group_id.in_(group_ids)
    ).all()

    for attribute in attributes:
        attr_info = m.AttributeGroupAttribute.query.filter(
            m.AttributeGroupAttribute.attribute_group_id.in_(group_ids),
            m.AttributeGroupAttribute.attribute_id == attribute.id
        ).first()
        setattr(attribute, 'attr_info', attr_info)

    return attributes or []


def get_or_new_option(option_value, attribute_object, auto_commit=True):
    """
    :type option_value: str
    :type attribute_object: m.Attribute
    :param option_value: Label for selection
    :param attribute_object
    :param auto_commit
    :return: option
    """

    attribute_id = attribute_object.id
    q = m.AttributeOption.query.filter(
        m.AttributeOption.value.ilike(str(option_value).lower()),
        m.AttributeOption.attribute_id == attribute_id
    )
    if attribute_object.code == UOM_CODE_ATTRIBUTE:
        if current_user.seller_id in config.SELLER_ONLY_UOM:
            q = q.filter(m.AttributeOption.seller_id == current_user.seller_id)
        else:
            q = q.filter(m.AttributeOption.seller_id.notin_(config.SELLER_ONLY_UOM))
    option = q.first()
    if option:
        return option

    if attribute_object.code == UOM_CODE_ATTRIBUTE:
        return None

    option = m.AttributeOption()
    option.attribute_id = attribute_id
    option.value = option_value

    m.db.session.add(option)
    if auto_commit:
        m.db.session.commit()
    else:
        m.db.session.flush()
    return option
