#coding=utf-8

from operator import itemgetter
from sqlalchemy import func
from catalog import utils
from catalog.services import Singleton
from catalog import models as m
from catalog.services.attribute_sets import AttributeSetBaseService
from catalog.extensions import exceptions as exc


class AttributeSetConfigService(Singleton, AttributeSetBaseService):
    def update_attribute_set_config(self, config_id, data):
        field_displays = []
        seo_configs = m.Misc.query.filter(
            m.Misc.type == 'seo_config'
        )
        seo_configs_code_list = [s.code for s in seo_configs]
        for item in data:
            field_display = item.get('field_display')
            if field_display not in seo_configs_code_list:
                raise exc.BadRequestException('field_display không hợp lệ')
            field_displays.append(field_display)

        m.AttributeSetConfigDetail.query.filter(
            m.AttributeSetConfigDetail.attribute_set_config_id == config_id,
            m.AttributeSetConfigDetail.field_display.in_(field_displays),
        ).delete(False)
        return self.create_new(data, config_id)

    def create_new(self, data, config_id):
        ret = list()
        try:
            for display in data:
                if display.get('detail'):
                    # Check priority unique in detail list
                    priority_list = [d.get('priority') for d in display.get('detail') if d.get('priority')]
                    if priority_list and utils.list_has_duplicates(priority_list):
                        raise exc.BadRequestException('Priority không được trùng nhau')

                    for detail_input in display.get('detail'):
                        # Handle constrain between SEO config & attribute
                        seo_object_types = m.Misc.query.filter(
                            m.Misc.type == 'seo_object_type'
                        )
                        seo_object_types_code_list = [s.code for s in seo_object_types]
                        if detail_input['object_type'] not in seo_object_types_code_list:
                            raise exc.BadRequestException('Data truyền lên không hợp lệ')
                        if detail_input['object_type'] == 'text':
                            if not detail_input['object_value'].strip():
                                raise exc.BadRequestException('Nội dung Text không được bỏ trống')
                            if len(detail_input['object_value']) > 255:
                                raise exc.BadRequestException('Nội dung Text không được quá 255 ký tự')
                        if (detail_input['text_before'] and len(detail_input['text_before']) > 255) or (
                                detail_input['text_after'] and len(detail_input['text_after']) > 255):
                            raise exc.BadRequestException('Ký tự trước/sau không được quá 255 ký tự')
                        if detail_input['object_type'] == 'attribute':
                            self.allow_config_detail(
                                config_id,
                                detail_input['object_value']
                            )

                        detail_input['attribute_set_config_id'] = config_id
                        detail_input['field_display'] = display.get('field_display')
                        detail = m.AttributeSetConfigDetail(**detail_input)
                        ret.append(detail)
                        m.db.session.add(detail)
            m.db.session.commit()
        except Exception as e:
            m.db.session.rollback()
            raise e
        else:
            return ret

    def allow_config_detail(self, attribute_set_config_id, attribute_id):
        """
        :param attribute_set_config_id:
        :param attribute_id:
        :type attribute_id: int
        :type attribute_id: int
        :return:
        """
        config = m.AttributeSetConfig.query.get(
            attribute_set_config_id
        )  # type: m.AttributeSetConfig

        self.attribute_in_attribute_set(config.attribute_set_id, attribute_id)

    def create_config(self, data):
        try:
            if data.get('config_default_id') is None:
                self._create_default_config(data.get('attribute_set_id'))

            check_attr_list = []

            optional_list = data.get('optional_list')
            optional_list_ids = [ol.get('id') for ol in optional_list if ol.get('id')]

            # Sort optional list by is_deleted to delete config first, then check except deleted config
            for option in sorted(optional_list, key=itemgetter('is_deleted'), reverse=True):
                self._check_attribute_in_attribute_set(
                    data.get('attribute_set_id'),
                    option.get('attributes')
                )
                config = self._get_or_new_config(data.get('attribute_set_id'), option.get('id'))

                # Check if brand is invalid
                brand = m.Brand.query.filter(
                    m.Brand.id == option.get('brand_id')
                ).first()
                if option.get('brand_id') and not brand:
                    raise exc.BadRequestException('Thương hiệu không tồn tại')

                # Check if attribute list is not sync
                attr_id_list = [a.get('id') for a in option.get('attributes')]
                if check_attr_list and check_attr_list != attr_id_list:
                    raise exc.BadRequestException('Thuộc tính truyền lên không khớp giữa các config')
                else:
                    check_attr_list = attr_id_list

                # Check if new/update config is duplicate with exist config
                self._check_config_is_duplicate(data.get('attribute_set_id'), option, optional_list_ids)
                if option.get('id'):  # If not duplicate, remove from optional_list_ids for next checking
                    optional_list_ids.remove(option.get('id'))

                config.brand_id = option.get('brand_id')
                config.is_deleted = option.get('is_deleted')
                config = self._set_config_attribute(config, option.get('attributes'))
                m.db.session.add(config)

            attribute_set = m.AttributeSet.query.get(data.get('attribute_set_id'))
            attribute_set.updated_at = func.now()
            m.db.session.add(attribute_set)
            m.db.session.commit()
        except Exception as e:
            m.db.session.rollback()
            raise e
        else:
            return self.get_config_list(data['attribute_set_id'])

    def get_config_detail_common(self, config_id):
        config = m.AttributeSetConfig.query.get(config_id)
        if config is None:
            raise exc.BadRequestException('Config ID incorrect')
        return config

    def get_config_list(self, attribute_set_id):
        NUMBER_OF_ATTR_IN_CONFIG = 5
        def format_response(attribute_set_configs):
            result = {
                'config_default_id': None,
                'optional_list': list()
            }
            for as_config in attribute_set_configs:
                #@TODO: ???
                if as_config.is_default == 1:
                    result['config_default_id'] = as_config.id
                    continue
                attributes = [{
                    'id': getattr(as_config, f'attribute_{attr_index}_id'),
                    'value': getattr(as_config, f'attribute_{attr_index}_value')
                } for attr_index in range(1, NUMBER_OF_ATTR_IN_CONFIG+1)]
                result['optional_list'].append({
                    'id': as_config.id,
                    'brand_id': as_config.brand_id,
                    'attributes': attributes
                })
            return result

        result = m.AttributeSetConfig.query.filter(
            m.AttributeSetConfig.attribute_set_id == attribute_set_id,
            m.AttributeSetConfig.is_deleted == 0,
        )
        return format_response(result)

    def _get_int_or_string(self, value):
        try:
            return int(value)
        except ValueError:
            return value

    def _modify_config(self, config, res):
        field_display = config.field_display
        if config.object_type == 'attribute':
            config.object_value = self._get_int_or_string(config.object_value)
        if field_display not in res:
            res[field_display] = {
                'field_display': field_display,
                'detail': []
            }
        return config, res

    def format_config_data(self, configs):
        res = {}
        for config in configs:
            config, res = self._modify_config(config, res)
            res[config.field_display]['detail'].append(config)
        return [v for k, v in res.items()]

    def get_config_detail(self, config_id, field_display=None):
        configs = m.AttributeSetConfigDetail.query
        if field_display:
            configs = configs.filter(
                m.AttributeSetConfigDetail.field_display.in_(
                    field_display.split(',')
                )
            )
        configs = configs.filter(
            m.AttributeSetConfigDetail.attribute_set_config_id == config_id,
        )
        configs.all()
        return {
            'detail': configs
        }
