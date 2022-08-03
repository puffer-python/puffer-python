# coding=utf-8

from sqlalchemy import or_
from catalog import utils
from catalog import models as m
from catalog.extensions import exceptions as exc


class AttributeSetBaseService:
    def _save_group(self, attribute_set_id, group_data, variation_attributes=[]):
        """
        Save attribute groups to db.

        :param attribute_set_id:
        :param group_data:
        :return:
        """
        group = m.AttributeGroup()
        group_name = group_data.get('name')
        group.name = group_name
        group.code = utils.slugify(group_name)
        group.attribute_set_id = attribute_set_id
        group.priority = group_data.get('priority')
        group.is_flat = group_data.get('is_flat')
        group.path = ''
        group.system_group = group_data.get('system_group')
        attributes_data = group_data.get('attributes')
        m.db.session.add(group)
        m.db.session.flush()
        self._save_group_attribute_config(group.id, attributes_data, variation_attributes)
        return group

    def _save_group_attribute_config(self, group_id, attributes_data, variation_attributes=[]):
        """
        Save attribute config to attribute_group_attribute table.

        :param group_id:
        :param attributes_data:
        :return:
        """
        for attr_data in attributes_data:
            gr_attr = m.AttributeGroupAttribute()
            gr_attr.attribute_group_id = group_id
            gr_attr.attribute_id = attr_data.get('id')
            gr_attr.priority = attr_data.get('priority')
            gr_attr.highlight = attr_data.get('highlight')
            gr_attr.text_before = attr_data.get('text_before')
            gr_attr.text_after = attr_data.get('text_after')
            gr_attr.is_displayed = attr_data.get('is_displayed')
            gr_attr.is_variation = 1 if gr_attr.attribute_id in variation_attributes else 0
            m.db.session.add(gr_attr)

    def _update_system_group(self, group, group_data):
        group.priority = group_data.get('priority')
        group.is_flat = group_data.get('is_flat')
        attributes_data = group_data.get('attributes')
        self._update_system_group_attribute_config(group.id, attributes_data)
        return group

    def _update_system_group_attribute_config(self, group_id, attributes_data):
        old_gr_attributes = m.AttributeGroupAttribute.query.filter(
            m.AttributeGroupAttribute.attribute_group_id == group_id).all()
        for attr_data in attributes_data:
            gr_attr = next(filter(lambda x: x.attribute_id == attr_data.get('id'), old_gr_attributes), None)
            if gr_attr:
                gr_attr.priority = attr_data.get('priority')
                gr_attr.highlight = attr_data.get('highlight')
                gr_attr.text_before = attr_data.get('text_before')
                gr_attr.text_after = attr_data.get('text_after')
                gr_attr.is_displayed = attr_data.get('is_displayed')

    def _remove_attribute_set_configs(self, attribute_set_id):
        """
        Xóa toàn bộ thông tin attribute group và attribute set trong các bảng
        dữ liệu attribute_groups, attribute_group_attribute.

        :param attribute_set_id:
        :return:
        """
        groups = m.AttributeGroup.query.filter(m.AttributeGroup.attribute_set_id == attribute_set_id).all()
        group_ids = list(map(lambda x: x.id, groups))
        not_system_group_ids = list(map(lambda x: x.id, filter(lambda x: not x.system_group, groups)))

        # get list attribute_group_attribute is variation
        variation_attributes = m.AttributeGroupAttribute.query.filter(
            m.AttributeGroupAttribute.is_variation == 1,
            m.AttributeGroupAttribute.attribute_group_id.in_(group_ids)
        ).all()
        variation_attributes_set = [v.attribute_id for v in variation_attributes]

        if not_system_group_ids:
            # remove attribute_group_attribute
            m.AttributeGroupAttribute.query.filter(
                m.AttributeGroupAttribute.attribute_group_id.in_(not_system_group_ids)
            ).delete(synchronize_session='fetch')
            # remove attribute_groups
            m.AttributeGroup.query.filter(m.AttributeGroup.id.in_(not_system_group_ids)).delete(
                synchronize_session='fetch')
            m.db.session.flush()

        return variation_attributes_set

    def _check_seo_config_detail(self, attribute_set_id, ids):
        config_detail = m.AttributeSetConfigDetail.query.join(
            m.AttributeSetConfig
        ).filter(
            m.AttributeSetConfig.attribute_set_id == attribute_set_id,
            m.AttributeSetConfigDetail.object_type == 'attribute',
            m.AttributeSetConfigDetail.object_value.notin_(ids),
            m.AttributeSetConfig.is_deleted == 0
        ).first()
        if config_detail:
            raise exc.BadRequestException('Không thể xóa thuộc tính đã cấu hình SEO')

    def _check_seo_config(self, attribute_set_id, attribute_set_configs):
        ids = []

        for attribute_group in attribute_set_configs:
            for attribute in attribute_group.get('attributes'):
                ids.append(attribute.get('id'))

        # Query to check if there is a duplicate config
        conditions = []
        for i in range(5):
            attr_id_field = eval('m.AttributeSetConfig.attribute_%s_id' % (i + 1))
            conditions.append(attr_id_field.notin_(ids))

        query = m.AttributeSetConfig.query.filter(
            m.AttributeSetConfig.attribute_set_id == attribute_set_id,
            m.AttributeSetConfig.is_default == None,
            m.AttributeSetConfig.is_deleted == 0,
            or_(*conditions)
        )

        self._check_seo_config_detail(attribute_set_id, ids)
        res = query.first()

        if res:
            raise exc.BadRequestException('Không thể xóa thuộc tính đã cấu hình SEO')

    def _check_seo_config_detail(self, set_id, ids):
        config_detail = m.AttributeSetConfigDetail.query.join(
            m.AttributeSetConfig
        ).filter(
            m.AttributeSetConfig.attribute_set_id == set_id,
            m.AttributeSetConfigDetail.object_type == 'attribute',
            m.AttributeSetConfigDetail.object_value.notin_(ids),
            m.AttributeSetConfig.is_deleted == 0
        ).first()
        if config_detail:
            raise exc.BadRequestException('Không thể xóa thuộc tính đã cấu hình SEO')

    def _create_default_config(self, set_id):
        config = m.AttributeSetConfig.query.filter(
            m.AttributeSetConfig.attribute_set_id == set_id,
            m.AttributeSetConfig.is_default == 1
        ).first()

        if config:
            return config

        config = m.AttributeSetConfig(
            attribute_set_id=set_id,
            is_default=1
        )
        m.db.session.add(config)
        m.db.session.commit()

    def attribute_in_attribute_set(self, set_id, attribute_id):
        group_attribute = m.AttributeGroupAttribute.query.join(
            m.AttributeGroup
        ).filter(
            m.AttributeGroup.attribute_set_id == set_id,
            m.AttributeGroupAttribute.attribute_id == attribute_id
        ).first()
        if group_attribute is None:
            raise exc.BadRequestException(
                'Thuộc tính {} không tồn tại trong bộ thuộc tính {}'.format(attribute_id, set_id))

    def _check_attribute_in_attribute_set(self, set_id, attributes):
        """
        :type attributes: list[dict]
        :type set_id: int
        :param set_id:
        :param attributes:
        :return:
        """
        for attribute in attributes:
            self.attribute_in_attribute_set(set_id, attribute.get('id'))

    def _get_or_new_config(self, attribute_set_id, config_id=None):
        if config_id is None:
            return m.AttributeSetConfig(
                attribute_set_id=attribute_set_id
            )
        config = m.AttributeSetConfig.query.filter(
            m.AttributeSetConfig.id == config_id,
            m.AttributeSetConfig.attribute_set_id == attribute_set_id
        ).first()
        if config is None:
            raise exc.BadRequestException('Config ID not found')
        return config

    def _check_config_is_duplicate(self, set_id, option, optional_list_ids):
        """
        Check if new/update config is duplicate with exist config in DB
        :param set_id: attribute set id
        :param option: config to check
        :param optional_list_ids: list id (if exist) to check query
        :return:
        """

        # -- Query to check if there is a duplicate config
        conditions = []
        if option.get('id'):
            conditions.append(m.AttributeSetConfig.id.notin_(optional_list_ids))
            conditions.append(m.AttributeSetConfig.id != option.get('id'))
        # Check brand_id
        if option.get('brand_id'):
            conditions.append(or_(
                m.AttributeSetConfig.brand_id == option.get('brand_id'),
                m.AttributeSetConfig.brand_id == None
            ))
        query = m.AttributeSetConfig.query.filter(
            m.AttributeSetConfig.attribute_set_id == set_id,
            m.AttributeSetConfig.is_default == None,
            m.AttributeSetConfig.is_deleted == 0,
            *conditions
        )
        # Check attribute_x_id, attribute_x_value
        for i in range(5):
            attr_id = None
            attr_value = None
            if len(option.get('attributes')) > i:
                attr_id = option.get('attributes')[i].get('id')
                attr_value = option.get('attributes')[i].get('value')

            attr_id_field = eval('m.AttributeSetConfig.attribute_%s_id' % (i + 1))
            attr_value_field = eval('m.AttributeSetConfig.attribute_%s_value' % (i + 1))
            query = query.filter(
                attr_id_field == attr_id,
                attr_value_field == attr_value
            )
        exist_config = query.first()
        if exist_config and option.get('is_deleted') == 0:
            raise exc.BadRequestException('Cấu hình bị trùng lặp')

    def _set_config_attribute(self, config, param):
        for i in range(5):
            setattr(config, 'attribute_%s_id' % (i + 1), None)
            setattr(config, 'attribute_%s_value' % (i + 1), None)
            if len(param) > i:
                attr_id = param[i].get('id')
                attr_value = param[i].get('value')

                # Check if attr_value is not in list option of this attribute
                options = m.AttributeOption.query.filter(
                    m.AttributeOption.attribute_id == attr_id
                ).all()
                if options:
                    option_ids = [o.id for o in options]
                    if attr_value not in option_ids and not config.is_deleted:
                        raise exc.BadRequestException('Giá trị {} không tồn tại trong thuộc tính'.format(attr_value))

                setattr(
                    config,
                    'attribute_%s_id' % (i + 1),
                    attr_id
                )
                setattr(
                    config,
                    'attribute_%s_value' % (i + 1),
                    attr_value
                )
        return config
