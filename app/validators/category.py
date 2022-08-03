# coding=utf-8
import re
import sqlalchemy as sa
from flask_login import current_user
from sqlalchemy import or_

from catalog.utils.validation_utils import validate_a_list_required
from catalog.utils.category import calculate_maximal_children_depth
from catalog.validators import Validator
from catalog.extensions import exceptions as exc
from catalog import models
from catalog.constants import CATEGORY_MAX_DEPTH
from catalog.services.categories import CategoryQuery
from catalog.services import seller as seller_srv


class GetCategoryTreeValidator(Validator):
    @staticmethod
    def validate_category_id(category_id, **kwargs):
        category = models.Category.query.filter(
            models.Category.id == category_id
        ).options(
            sa.orm.load_only('is_active')
        ).first()
        if not category:
            raise exc.BadRequestException('Danh mục không tồn tại')
        if not category.is_active:
            raise exc.BadRequestException('Danh mục đang vô hiệu')

        return category


class GetCategoryRecommendationValidator(Validator):
    @staticmethod
    def validate_category_id(category_id, **kwargs):
        category = models.Category.query.filter(
            models.Category.id == category_id,
            models.Category.seller_id == current_user.seller_id
        ).first()

        if not category or not category.is_active:
            raise exc.BadRequestException('Danh mục ngành hàng {} không tồn tại'.format(category_id))

        root = category if not category.root else category.root
        if root.master_category_id is None:
            raise exc.BadRequestException(f'Danh mục cha {root.name} cần được đồng bộ trước')


class CreateCategoryValidator(Validator):
    @staticmethod
    def validate_category_create(name, code, manage_serial, **kwargs):
        # validate parent category
        parent_id = kwargs.get("parent_id")
        if parent_id and parent_id != 0:
            parent: models.Category = validate_node_existence(parent_id)
            if not parent.is_active:
                raise exc.BadRequestException("Không thể tạo danh mục con cho danh mục vô hiệu")
            if parent.depth >= CATEGORY_MAX_DEPTH:
                raise exc.BadRequestException("Không thể tạo danh mục con cho danh mục có độ sâu >= 6")
            if category_has_product(parent):
                raise exc.BadRequestException("Không thể tạo danh mục con cho danh mục đã có sản phẩm")
        
        # check name and code existence
        validate_name_and_code_duplicate(name, code, parent_id)
        _validate_code(code)

        # validate serial
        auto_generate_serial = kwargs.get("auto_generate_serial")
        if not manage_serial and auto_generate_serial:
            raise exc.BadRequestException("Không set tự động sinh serial nếu quản lí serial là vô hiệu")
        if (manage_serial and auto_generate_serial is None):
            raise exc.BadRequestException("Thiếu tự động sinh serial")
        # validate tax Code
        if kwargs.get('tax_in_code') is not None:
            validate_tax_code_existence(kwargs.get('tax_in_code'))
        if kwargs.get('tax_out_code') is not None:
            validate_tax_code_existence(kwargs.get('tax_out_code'))

        # validate unit and attribute set
        attribute_set_id = kwargs.get("attribute_set_id")
        if attribute_set_id:
            validate_attribute_set_id(attribute_set_id)
        #validate attribute_set_id is required if category is level 1
        elif not parent_id:
            raise exc.BadRequestException("Thông tin nhóm sản phẩm là bắt buộc nếu không có thông tin danh mục cha")

        # validate master_category mapping
        master_category_id = kwargs.get("master_category_id")
        if master_category_id is not None:
            validate_master_category_id(master_category_id)

        if kwargs.get('unit_id') is not None:
            validate_unit_id(kwargs.get("unit_id"))

        # validate shipping_type
        shipping_types = kwargs.get('shipping_types')
        if shipping_types:
            validate_a_list_required(
                obj_model=models.ShippingType,
                list_input=shipping_types,
                field='id',
                apply_is_active=True,
                message='Shipping type không tồn tại hoặc đã bị vô hiệu'
            )


class UpdateCategoryValidator(Validator):
    @staticmethod
    def validate_update_category(**kwargs):
        if len(kwargs) == 1:
            raise exc.BadRequestException("Không có dữ liệu cập nhật")

        # validate obj_id
        obj_id = kwargs.get("obj_id")
        current_node: models.Category = validate_node_existence(obj_id)

        # validate active
        is_active = kwargs.get("is_active")
        if is_active:
            check_parent_node_active(current_node)
        if is_active is False:
            check_child_node_active(current_node)
            validate_exist_product_with_inactive_category(current_node)

        # validate parent category
        parent_id = kwargs.get("parent_id")
        if parent_id and parent_id != 0:
            parent_node: models.Category = validate_node_existence(parent_id)
            if parent_id == obj_id:
                raise exc.BadRequestException("Danh mục cha không phù hợp")

            ancestral_ids = set(
                int(id_str)
                for id_str in parent_node.path.split("/")
            )
            is_potential_cyclic = (current_node.id in ancestral_ids)
            if is_potential_cyclic:
                raise exc.BadRequestException("Không thể cài đặt một danh mục đang thuộc chính nó làm danh mục cha")

            if not parent_node.is_active and current_node.is_active:
                raise exc.BadRequestException("Không thể chuyển danh mục hiệu lực sang danh mục vô hiệu")

            depth_from_current = calculate_maximal_children_depth(category=current_node)
            # current_node is A: [A] -> B -> C -> D
            # -> potential depth of [A]: 4
            # parent_node is Z: X -> Y -> [Z]
            # -> depth of [Z]: 3
            # If [A] gets appended to [Z], the depth of D becomes 7, which is invalid;
            # therefore, we must check potential depth from current_node,
            # and then add it to depth of parent_node.
            if parent_node.depth + depth_from_current > CATEGORY_MAX_DEPTH:
                raise exc.BadRequestException(f"Không cho phép cập nhật danh mục có độ sâu > {CATEGORY_MAX_DEPTH}")

        # check name and code existence
        name = kwargs.get("name")
        code = kwargs.get("code")
        if name or code:
            validate_name_and_code_duplicate_with_id(name, code, parent_id=parent_id, obj_id=obj_id)
        if code:
            _validate_code(code)

        # validate tax Code
        tax_in_code = kwargs.get("tax_in_code")
        tax_out_code = kwargs.get("tax_out_code")
        if tax_in_code is not None:
            validate_tax_code_existence(tax_in_code)
        if tax_out_code is not None:
            validate_tax_code_existence(tax_out_code)

        # validate serial
        manage_serial = kwargs.get("manage_serial", current_node.manage_serial)
        auto_generate_serial = kwargs.get("auto_generate_serial")
        if not manage_serial and auto_generate_serial:
            raise exc.BadRequestException(
                "Không set tự động sinh serial nếu quản lí serial là vô hiệu")

        # validate unit and attribute set
        attribute_set_id = kwargs.get("attribute_set_id")
        is_adult = kwargs.get("is_adult")
        if attribute_set_id:
            validate_attribute_set_id(attribute_set_id)
        elif not parent_id and is_adult is None:
            raise exc.BadRequestException("Thông tin nhóm sản phẩm là bắt buộc nếu không có thông tin danh mục cha")
        unit_id = kwargs.get("unit_id")
        if unit_id is not None:
            validate_unit_id(kwargs.get("unit_id"))

        # validate master_category mapping
        master_category_id = kwargs.get("master_category_id")
        if master_category_id is not None:
            validate_master_category_id(master_category_id)

        # validate shipping_types
        shipping_types = kwargs.get('shipping_types')
        if shipping_types:
            validate_a_list_required(
                obj_model=models.ShippingType,
                list_input=shipping_types,
                field='id',
                apply_is_active=True,
                message='Shipping type không tồn tại hoặc đã bị vô hiệu'
            )


def validate_exist_product_with_inactive_category(current_node):
    if category_has_product(current_node):
        raise exc.BadRequestException('Không vô hiệu được ngành hàng có sản phẩm')


def category_has_product(cat):
    result = models.db.session.query(
        models.db.session.query(models.ProductCategory).filter_by(category_id=cat.id).exists()
    ).scalar()
    return bool(result)

def validate_node_existence(category_id):
    category = models.Category.query.filter(
        models.Category.id == category_id,
        models.Category.seller_id == current_user.seller_id,
    ).first()
    if not category:
        raise exc.BadRequestException('Danh mục {} không tồn tại'.format(category_id))
    return category


def validate_name_and_code_duplicate(name, code, parent_id):
    """
    Validate for api create category
    :param code:
    :param name:
    :param parent_id:
    :return:
    """
    existed = models.Category.query.filter(
        or_(
            models.Category.code == code
        ),
        models.Category.seller_id == current_user.seller_id
    ).first()
    if existed:
        raise exc.BadRequestException('Mã danh mục đã tồn tại trong hệ thống')

    existed = models.Category.query.filter(
        models.Category.name == name,
        models.Category.parent_id == parent_id,
        models.Category.seller_id == current_user.seller_id,
        models.Category.is_active == 1
    ).first()
    if existed:
        raise exc.BadRequestException('Tên danh mục cùng danh mục cha đã tồn tại trong hệ thống')


def validate_name_and_code_duplicate_with_id(name, code, parent_id, obj_id):
    """
    Validate for api update category
    :param name:
    :param code:
    :param parent_id:
    :param obj_id:
    :return:
    """
    existed = models.Category.query.filter(
        models.Category.code == code,
        models.Category.id != obj_id,
        models.Category.seller_id == current_user.seller_id
    ).first()
    if existed:
        raise exc.BadRequestException('Mã danh mục đã tồn tại trong hệ thống')

    existed = models.Category.query.filter(
        models.Category.name == name,
        models.Category.parent_id == parent_id,
        models.Category.seller_id == current_user.seller_id,
        models.Category.id != obj_id,
        models.Category.is_active == 1
    ).first()
    if existed:
        raise exc.BadRequestException('Tên danh mục cùng danh mục cha đã tồn tại trong hệ thống')


def validate_tax_code_existence(tax_code):
    tax = models.Tax.query.filter(
        models.Tax.code == tax_code,
    ).first()
    if not tax:
        raise exc.BadRequestException('Mã thuế không tồn tại')


def check_child_node_active(current_node):
    for child_node in current_node.children:
        if child_node.is_active:
            raise exc.BadRequestException("Không thể vô hiệu danh mục có danh mục đang hoạt động")


def check_parent_node_active(current_node):
    parent_node = current_node.parent
    if parent_node and not parent_node.is_active:
        raise exc.BadRequestException("Không thể active danh mục có danh mục cha vô hiệu")


def validate_unit_id(unit_id):
    unit = models.Unit.query.get(unit_id)
    if not unit:
        raise exc.BadRequestException("Đơn vị tính không tồn tại")


def validate_attribute_set_id(attribute_set_id):
    attribute_set = models.AttributeSet.query.get(attribute_set_id)
    if not attribute_set:
        raise exc.BadRequestException("Bộ thuộc tính không tồn tại")


def _validate_code(code):
    pattern = re.compile("^[A-Za-z0-9-_.]+$")
    if pattern.match(code):
        pass
    else:
        raise exc.BadRequestException("Mã danh mục chỉ chứa các kí tự a-z A-Z 0-9 - _ .")


def validate_master_category_id(master_category_id):
    master_category = models.MasterCategory.query.filter(
        models.MasterCategory.id == master_category_id,
        models.MasterCategory.is_active.is_(True)
    ).first()

    if master_category is None:
        raise exc.BadRequestException('Danh mục sản phẩm không tồn tại')


class GetCategoryValidator(Validator):
    @staticmethod
    def validate_category_id(category_id, seller_id, **kwargs):
        category = CategoryQuery().restrict_by_seller(seller_id).apply_filters({'id': category_id}).first()
        if not category:
            raise exc.BadRequestException("Danh mục ngành hàng không tồn tại")


class CloneMasterCategory(Validator):
    @staticmethod
    def validate_top_level_master_category_ids(master_category_ids, **kwargs):
        master_category_ids_in_db = [master_category.id for master_category in models.MasterCategory.query.filter(
            models.MasterCategory.id.in_(master_category_ids),
            models.MasterCategory.is_active == 1,
            models.MasterCategory.parent_id == 0
        ).all()]

        if len(master_category_ids) != len(master_category_ids_in_db):
            invalid_master_category_ids = []
            for master_category_id in master_category_ids:
                if master_category_id not in master_category_ids_in_db:
                    invalid_master_category_ids.append(master_category_id)

            raise exc.BadRequestException(
                f'Các danh mục sau không khả dụng hoặc không tồn tại: {invalid_master_category_ids}')

    @staticmethod
    def validate_seller_id(seller_id, **kwargs):
        seller = seller_srv.get_seller_by_id(seller_id)
        if not seller:
            raise exc.BadRequestException('Seller không tồn tại')
