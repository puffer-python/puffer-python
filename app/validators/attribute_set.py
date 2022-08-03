# coding=utf-8

import re

import funcy
from sqlalchemy import exists
from catalog import (
    models,
    utils,
)
from catalog.services.attribute_sets import AttributeSetService
from catalog.extensions import exceptions as exc
from . import Validator

service = AttributeSetService.get_instance()


class AttributeSetCreateValidator(Validator):
    @staticmethod
    def validate_name(name, **kwargs):
        if utils.contain_special_char(name):
            raise exc.BadRequestException('Tên bộ thuộc tính không hợp lệ')

        a = models.AttributeSet.query.filter(models.AttributeSet.name == name).first()
        if a is not None:
            raise exc.BadRequestException('Attribute set đã tồn tại')


class GetAttributeSetListValidator(Validator):
    @staticmethod
    def validate_params(params, **kwargs):
        by_supported = ('id', 'name', 'created_at', 'updated_at')
        order_supported = ('asc', 'desc')
        sort_field = params.get('sort_field')
        if sort_field and sort_field not in by_supported:
            raise exc.BadRequestException(
                f'Chỉ sắp xếp theo cá trường {", ".join(by_supported)}')

        sort_order = params.get('sort_order')
        if not sort_order and sort_order:
            raise exc.BadRequestException('Chưa chọn thuộc tính để sắp xếp')
        if sort_order and sort_order not in order_supported:
            raise exc.BadRequestException(
                f'Chỉ chọn một trong các giá trị {", ".join(order_supported)}')


class Attribute(object):
    """
    Mô phỏng 1 attribute trong tập dữ liệu
    """

    def __init__(self, attr_id, priority):
        self.id = attr_id
        self.priority = priority


class Group(object):
    """
    Mô phỏng 1 group trong tập dữ liệu
    """

    def __init__(self, **kwargs):
        self.temp_id = kwargs.pop('temp_id')
        self.priority = kwargs.pop('priority')
        self.name = kwargs.pop('name')
        self.parent_id = kwargs.pop('parent_id')
        self.is_flat = kwargs.pop('is_flat')
        self.level = kwargs.pop('level')
        self.attributes = self._create_attributes(kwargs.pop('attributes'))
        self.subgroups = []
        self.system_group = kwargs.pop('system_group')

    def _create_attributes(self, data):
        attributes = []
        for attr_data in data:
            attribute = Attribute(
                attr_id=attr_data['id'],
                priority=attr_data['priority']
            )
            if attribute.id in attributes:
                raise exc.BadRequestException(f'Duplicate attribute {attribute.id}')
            attributes.append(attribute)

        return attributes

    @property
    def max_priority(self):
        """
        Return max priority of a group

        :return:
        """
        max_pr = self.priority or 0
        for attribute in self.attributes:
            if attribute.priority > max_pr:
                max_pr = attribute.priority

        return max_pr

    def add_subgroup(self, group):
        """
        Add new child group.

        :param group:
        :return:
        """
        self.subgroups.append(group)


class UpdateAttributeSetValidator(Validator):
    @classmethod
    def _get_parent_group(cls, parent_id, group_id, groups):
        if parent_id == group_id:
            pass
        for group in groups:
            if group.temp_id == parent_id:
                return group

        raise exc.BadRequestException('Group %s has invalid parent_id' % group_id)

    @classmethod
    def _assign_subgroups(cls, groups):
        for group in groups:
            parent_id = group.parent_id
            if parent_id:
                parent = cls._get_parent_group(parent_id, group.temp_id, groups)
                parent.add_subgroup(group)

        return groups

    @classmethod
    def _create_groups(cls, data):
        groups = []
        attributes = []
        for gr_data in data:
            group = Group(**gr_data)
            groups.append(group)
            attributes.extend(group.attributes)
        groups = cls._assign_subgroups(groups)
        return groups, attributes

    @classmethod
    def _check_unique_attributes(cls, attributes):
        """
        Check for uniqueness of attribute list.
        :param attributes:
        :return:
        """
        unique = set()
        for attribute in attributes:
            if attribute.id in unique:
                raise exc.BadRequestException(f'Duplicate attribute {attribute.id}')
            unique.add(attribute.id)
            unique.add(attribute.id)

    @classmethod
    def _check_duplicate_group_code(cls, groups):
        """
        Check for uniqueness of group names/codes.
        :param groups:
        :return:
        """
        unique = set()
        for group in groups:
            code = utils.convert(utils.slugify(group.name))
            if code in unique:
                raise exc.BadRequestException(
                    f'Group name {group.name} already existed')
            unique.add(code)

    @classmethod
    def _is_valid_group_config(cls, group):
        """
        A group config is considered valid if:
            priority < all(attr_priorities)
        :type group Group
        :return:
        """
        for attribute in group.attributes:
            attr = models.Attribute.query.get(attribute.id)
            if not attr:
                raise exc.BadRequestException(
                    f'Không tồn tại thuộc tính có id {attribute.id}')
            if attribute.priority is not None and int(attribute.priority) < int(group.priority or 0):
                raise exc.BadRequestException(
                    f'Invalid order of priority of group {group.temp_id}.')

        return True

    @classmethod
    def _validate_flat_display(cls, group):
        """
        If group has any child, is_flat must be True. Otherwise, is_flat is False.
        :param Group group:
        :return:
        """
        if group.subgroups and not group.is_flat:
            raise exc.BadRequestException(f'Group {group.temp_id} should be flat')

    @classmethod
    def _validate_group_priority_order(cls, this, groups):
        """
        Ensure correct visual order of an element in a set.
        For example, given two groups A and B with same level.
        If priority(A) < priority(B), then max_priority(A) < priority(B).
        :param this:
        :param groups:
        :return:
        """
        min_pr = this.priority
        max_pr = this.max_priority
        for other in groups:
            if other.level == this.level and other.temp_id != this.temp_id:
                if max_pr > other.priority > min_pr:
                    raise exc.BadRequestException(
                        'Invalid order of property of group {} and {}'.format(
                            this.temp_id, other.temp_id)
                    )
                elif other.priority < min_pr < other.max_priority:
                    raise exc.BadRequestException(
                        'Invalid order of property of group {} and {}'.format(
                            this.temp_id, other.temp_id)
                    )

    @classmethod
    def _validate_system_groups(cls, set_id, group):
        attribute_group = models.AttributeGroup.query.filter(models.AttributeGroup.attribute_set_id == set_id,
                                                             models.AttributeGroup.id == group.temp_id).first()
        if not attribute_group or not attribute_group.system_group:
            return True
        old_groups = models.AttributeGroupAttribute.query.filter(
            models.AttributeGroupAttribute.attribute_group_id == group.temp_id).all()
        old_attribute_ids = list(map(lambda x: x.attribute_id, old_groups))
        old_attribute_ids.sort(key=lambda x: x)
        new_attribute_ids = list(map(lambda x: x.id, group.attributes))
        new_attribute_ids.sort(key=lambda x: x)
        if str(old_attribute_ids) != str(new_attribute_ids):
            raise exc.BadRequestException(f'Group {group.name} bị thay đổi thuộc tính')

    @classmethod
    def validate_data(cls, set_id, data, **kwargs):
        groups, attributes = cls._create_groups(data['attribute_groups'])
        # an attribute can only appear once in a set
        cls._check_unique_attributes(attributes)
        # same encoded names are not allowed
        cls._check_duplicate_group_code(groups)
        # validate visual order of groups and attributes
        for group in groups:
            if cls._is_valid_group_config(group):
                cls._validate_flat_display(group)
                cls._validate_group_priority_order(group, groups)
                cls._validate_system_groups(set_id, group)


class UpdateOrderVariationAttributeValidator(Validator):
    @staticmethod
    def validate_data(set_id, ids, **kwargs):
        attribute_set = models.AttributeSet.query.get(set_id)
        if not attribute_set:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')
        variation_attrs = service.get_attributes_with_filter(set_id, is_variation=True)
        if sorted(funcy.lpluck_attr('attribute_id', variation_attrs)) != sorted(ids):
            raise exc.BadRequestException("Thuộc tính đã bị gỡ ra Bộ thuộc tính. Vui lòng kiểm tra lại")


class CreateVariationAttributeValidator(Validator):
    __MAX_VARIANT_ATTRIBUTES_COUNT = 4

    @classmethod
    def validate_data(cls, set_id, attribute_id, variation_display_type, **data):
        cls._validate_attribute(set_id, attribute_id)
        cls._validate_display_type(variation_display_type)
        cls._validate_attribute_set(set_id)

    @classmethod
    def _validate_attribute_set(cls, set_id):
        """

        :param set_id:
        :return:
        """
        exist = models.db.session.query(exists().where(models.AttributeSet.id == set_id)).scalar()
        if not exist:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')

        variation_configs = models.AttributeGroupAttribute.query \
            .join(models.AttributeGroup).join(models.Attribute) \
            .filter(
            models.AttributeGroup.attribute_set_id == set_id,
            models.AttributeGroupAttribute.is_variation == 1,
            models.Attribute.value_type == 'selection'
        ).all()

        if len(variation_configs) >= cls.__MAX_VARIANT_ATTRIBUTES_COUNT:
            raise exc.BadRequestException(
                'Một bộ thuộc tính chỉ có tối đa 4 thuộc tính biến thể'
            )

    @classmethod
    def _validate_display_type(cls, display_type):
        """

        :param display_type:
        :return:
        """
        if display_type not in ['code', 'image', 'text']:
            raise exc.BadRequestException('Kiểu hiển thị biến thể không hợp lệ')

    @classmethod
    def _validate_attribute(cls, attribute_set_id, attribute_id):
        """

        :param attribute_set_id:
        :param attribute_id:
        :return:
        """
        attribute = models.Attribute.query.filter(
            models.Attribute.id == attribute_id
        ).first()
        if not attribute:
            raise exc.BadRequestException('Thuộc tính được chọn không tồn tại')
        if attribute.value_type != 'selection':
            raise exc.BadRequestException(
                'Thuộc tính biến thể phải có kiểu dữ liệu selection'
            )

        attr_config = models.AttributeGroupAttribute.query \
            .join(models.AttributeGroup) \
            .filter(
            models.AttributeGroupAttribute.attribute_id == attribute_id,
            models.AttributeGroup.attribute_set_id == attribute_set_id
        ) \
            .first()

        if not attr_config:
            raise exc.BadRequestException(
                "Thuộc tính đã bị gỡ ra Bộ thuộc tính. Vui lòng kiểm tra lại"
            )

        if attr_config.is_variation:
            raise exc.BadRequestException(
                'Thuộc tính đã được chọn làm biến thể'
            )


class ImportCreateProductBasicInfoValidator(Validator):
    @staticmethod
    def validate_attribute_set_id(attribute_set_id, **kwargs):
        attribute_set = models.AttributeSet.query.get(attribute_set_id)
        if not attribute_set:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')

        return attribute_set

    @staticmethod
    def validate_uom_attribute(attribute_set_id, **kwargs):
        attribute_set = kwargs.get('attribute_set', models.AttributeSet.query.get(attribute_set_id))
        attributes = attribute_set.get_variation_attributes()
        if len(attributes) < 2:
            raise exc.BadRequestException('Sản phẩm phải có biến thể là UOM và UOM Ratio')
        if len(attributes) > 2 or (
                len(attributes) == 2 and set([attributes[0].code, attributes[1].code]) != set(['uom', 'uom_ratio'])):
            raise exc.BadRequestException('Nhóm sản phẩm có biến thể khác UOM')

        return attributes
