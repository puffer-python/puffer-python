# coding=utf-8
import logging

import re
from sqlalchemy import func, or_, exists

from catalog import models as m, utils
from catalog.extensions import exceptions as exc

from . import Validator

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateSaleCategoryValidator(Validator):
    @staticmethod
    def validate_existence(name, code, **kwargs):
        """
        Check if sale category name and code already existed in DB
        :param name:
        :param code:
        :param kwargs:
        :return:
        """
        existed = m.SaleCategory.query.filter(
            or_(
                func.lower(m.SaleCategory.name) == utils.normalized(name),
                func.lower(m.SaleCategory.code) == utils.normalized(code)
            )
        ).first()

        if existed:
            raise exc.BadRequestException(
                'Danh mục đã tồn tại trong hệ thống'
            )

    @staticmethod
    def validate_parent(parent_id, **kwargs):
        """
        Check whether parent of sale category exist and valid
        :param parent_id:
        :param kwargs:
        :return:
        """
        if not parent_id:
            return

        parent = m.SaleCategory.query.filter(
            m.SaleCategory.id == parent_id
        ).first()
        if not parent:
            raise exc.BadRequestException(
                'Danh mục cha không tồn tại trong hệ thống'
            )
        if not parent.is_active or not has_valid_ancestor(parent.parent_id):
            raise exc.BadRequestException(
                'Không thể tạo danh mục con cho danh mục vô hiệu'
            )


def is_node_existed(node_id):
    return m.db.session.query(
        exists().where(m.SaleCategory.id == node_id)
    ).scalar()


def has_valid_ancestor(node_id):
    """

    :param node_id:
    :return:
    """
    ancestor = m.SaleCategory.query.filter(
        m.SaleCategory.id == node_id
    ).first()
    if not ancestor:
        return True

    return ancestor.is_active and has_valid_ancestor(ancestor.parent_id)


class UpdatePositionValidator(Validator):
    @staticmethod
    def validate_node_existence(id_node, parent_id, left_node_id, **kwargs):
        """
        Check whether current_note, parent_node and left_node exist or not
        :param id_node:
        :param parent_id:
        :param left_node_id:
        :param kwargs:
        :return:
        """
        sc = m.SaleCategory.query.filter(
            m.SaleCategory.id == id_node
        ).first()
        if not sc:
            raise exc.BadRequestException("Danh mục bán hàng không tồn tại")
        if not sc.is_active:
            raise exc.BadRequestException("Danh mục đang bị vô hiệu")
        if parent_id and not is_node_existed(parent_id):
            raise exc.BadRequestException(
                'Danh mục cha không tồn tại'
            )
        if left_node_id:
            if not is_node_existed(left_node_id):
                raise exc.BadRequestException(
                    'Left node không tồn tại'
                )
            else:
                left_node = m.SaleCategory.query.get(left_node_id)
                if left_node.parent_id != parent_id:
                    raise exc.BadRequestException(
                        'Left node không cùng cha'
                    )


class UpdateSaleCategoryValidator(Validator):
    @staticmethod
    def validate_image_url(image=None, **kwargs):
        """

        :param image:
        :param kwargs:
        :return:
        """
        if image is None:
            return
        img_pattern = r"(http(s?):)([/|.|\w|\s|-])*\.(?:jpg|jpeg|png)"
        if not re.match(img_pattern, image):
            raise exc.BadRequestException(
                "Định dạng ảnh không hợp lệ"
            )

    @staticmethod
    def validate_existence(sc_id, name=None, code=None, **kwargs):
        """

        :param sc_id:
        :param name:
        :param code:
        :param kwargs:
        :return:
        """
        if name is None and code is None:
            return
        conds = []
        if name is not None:
            name = utils.normalized(name)
            conds.append(func.lower(m.SaleCategory.name) == name)
        if code is not None:
            code = utils.normalized(code)
            conds.append(func.lower(m.SaleCategory.code) == code)
        category = m.SaleCategory.query.filter(
            m.SaleCategory.id != sc_id,
            or_(*conds)
        ).first()  # type: m.SaleCategory
        if category:
            raise exc.BadRequestException(
                "Danh mục bán hàng đã tồn tại %s %s" % (name, code)
            )

    @staticmethod
    def validate_valid_category(sc_id, is_active=None, **kwargs):
        """

        :param sc_id:
        :param is_active:
        :param kwargs:
        :return:
        """
        sc = m.SaleCategory.query.get(sc_id)
        if not sc:
            raise exc.BadRequestException(
                "Danh mục không tồn tại"
            )
        if is_active and not has_valid_ancestor(sc.id):
            raise exc.BadRequestException(
                "Danh mục cha không ở trạng thái hiệu lực"
            )
