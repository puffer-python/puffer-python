# coding=utf-8
import logging

import re
from sqlalchemy import func, or_, exists

from catalog import models as m, utils
from catalog.extensions import exceptions as exc

from . import Validator

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class CreateMasterCategoryValidator(Validator):
    @staticmethod
    def validate_existence(name, code, **kwargs):
        """
        Check if sale category name and code already existed in DB
        :param name:
        :param code:
        :param kwargs:
        :return:
        """
        existed = m.MasterCategory.query.filter(
            or_(
                func.lower(m.MasterCategory.name) == utils.normalized(name),
                func.lower(m.MasterCategory.code) == utils.normalized(code)
            )
        ).first()

        if existed:
            raise exc.BadRequestException(
                'Danh mục đã tồn tại trong hệ thống'
            )

    @staticmethod
    def validate_parent_id(parent_id=None, **kwargs):
        """
        Check whether parent of sale category exist and valid
        :param parent_id:
        :param kwargs:
        :return:
        """
        if not parent_id:
            return

        parent = m.MasterCategory.query.filter(
            m.MasterCategory.id == parent_id
        ).first()
        if not parent:
            raise exc.BadRequestException(
                'Danh mục cha không tồn tại trong hệ thống'
            )
        if not parent.is_active or not has_valid_ancestor(parent.parent_id):
            raise exc.BadRequestException(
                'Không thể tạo danh mục con cho danh mục vô hiệu'
            )

    @staticmethod
    def validate_tax_code(tax_in_code=None, tax_out_code=None, **kwargs):
        if tax_in_code is not None:
            tax_in = m.Tax.query.filter(m.Tax.code == tax_in_code).first()
            if not tax_in:
                raise exc.BadRequestException('Mã thuế vào không tồn tại')
        if tax_out_code is not None:
            tax_out = m.Tax.query.filter(m.Tax.code == tax_out_code).first()
            if not tax_out:
                raise exc.BadRequestException('Mã thuế ra không tồn tại')

    @staticmethod
    def validate_attribute_set_id(attribute_set_id=None, **kwargs):
        if attribute_set_id is None:
            return
        attribute_set = m.AttributeSet.query.get(attribute_set_id)
        if not attribute_set:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')

    @staticmethod
    def validate_serial(manage_serial=None, auto_generate_serial=None, **kwargs):
        if manage_serial is None and auto_generate_serial is None:
            return
        if manage_serial is None and auto_generate_serial is not None:
            raise exc.BadRequestException('Phải kích hoạt quản lí serial trước khi thiết lập tự động sinh serial')
        if not manage_serial and auto_generate_serial:
            raise exc.BadRequestException(
                "Không set tự động sinh serial nếu quản lí serial là vô hiệu")
        if manage_serial and auto_generate_serial is None:
            raise exc.BadRequestException("Thiếu tự động sinh serial")

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

def is_node_existed(node_id):
    return m.db.session.query(
        exists().where(m.MasterCategory.id == node_id)
    ).scalar()


def has_valid_ancestor(node_id):
    """

    :param node_id:
    :return:
    """
    ancestor = m.MasterCategory.query.filter(
        m.MasterCategory.id == node_id
    ).first()
    if not ancestor:
        return True

    return ancestor.is_active and has_valid_ancestor(ancestor.parent_id)


class UpdateMasterCategoryValidator(Validator):
    @staticmethod
    def validate_1_id(cat_id, **kwargs):
        category = m.MasterCategory.query.get(cat_id)
        if not category:
            raise exc.BadRequestException('Danh mục không tồn tại')

    @staticmethod
    def validate_existence(name=None, code=None, **kwargs):
        """
        Check if sale category name and code already existed in DB
        :param name:
        :param code:
        :param kwargs:
        :return:
        """
        cat_id = kwargs.get('cat_id')
        existed = m.MasterCategory.query.filter(
            m.MasterCategory.id != cat_id,
            or_(
                func.lower(m.MasterCategory.name) == utils.normalized(name) if name is not None else None,
                func.lower(m.MasterCategory.code) == utils.normalized(code) if code is not None else None
            )
        ).first()

        if existed:
            raise exc.BadRequestException(
                'Danh mục đã tồn tại trong hệ thống'
            )

    @staticmethod
    def validate_active(is_active=None, **kwargs):
        if is_active == False:
            root_id = kwargs['cat_id']
            sub_nodes = m.MasterCategory.query.filter(
                or_(
                    m.MasterCategory.path.like(f'{root_id}/%'),
                    m.MasterCategory.path.like(f'%/{root_id}/%'),
                ),
                m.MasterCategory.is_active.is_(True)
            ).count()
            if sub_nodes:
                raise exc.BadRequestException('Danh mục đang có danh mục con hiệu lực')
            products = m.Product.query.filter(
                m.Product.master_category_id == root_id
            ).count()
            if products:
                raise exc.BadRequestException('Danh mục đang có sản phẩm')
            sellables = m.SellableProduct.query.filter(
                m.SellableProduct.master_category_id == root_id
            ).count()
            if sellables:
                raise exc.BadRequestException('Danh mục đang có sản phẩm')


    validate_attribute_set_id = CreateMasterCategoryValidator.validate_attribute_set_id

    validate_tax_code = CreateMasterCategoryValidator.validate_tax_code

    validate_image_url = CreateMasterCategoryValidator.validate_image_url

    validate_serial = CreateMasterCategoryValidator.validate_serial

    validate_parent_id = CreateMasterCategoryValidator.validate_parent_id


class GetMasterCategoryValidator(Validator):
    validate_id = UpdateMasterCategoryValidator.validate_1_id


class GetMasterCategoryTreeValidator(Validator):
    @classmethod
    def validate_master_category_id(cls, master_category_id, **kwargs):
        cat = m.MasterCategory.query.get(master_category_id)
        if not cat:
            raise exc.BadRequestException('Danh mục không tồn tại')
