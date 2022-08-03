# coding=utf-8
import requests
from flask_login import current_user
from sqlalchemy import (
    or_,
    and_,
    not_, exists,
)
from sqlalchemy.orm import joinedload

import config
from catalog import models
from catalog.extensions import exceptions as exc
from . import Validator
from catalog.services import seller as seller_service
from catalog.services.products.variant import load_all_variant_attributes
from catalog.utils import safe_cast
from catalog import constants
from catalog.services.seller import get_default_platform_owner_of_seller


class CreateVariantValidator(Validator):
    @classmethod
    def format_data(cls, data):
        def _format_variant_attribute_values(variants):
            f_variants = []
            for v in variants:
                f_attributes = []
                attributes = v['attributes']
                for a in attributes:
                    val = a['value']
                    int_val = safe_cast(val, int)
                    if val == int_val:
                        val = int_val
                    f_attributes.append({
                        'id': a['id'],
                        'value': val
                    })
                f_variants.append({
                    'attributes': f_attributes,
                    'name': v.get('name')
                })
            return f_variants

        f_variants = _format_variant_attribute_values(data.get('variants') or [])
        f_data = {'product_id': data['product_id']}
        if 'variants' in data:
            f_data['variants'] = f_variants
        return f_data

    @classmethod
    def validate_attribute(cls, data, **kwargs):
        """Kiếm tra không cho phép 2 biến thể có danh sách thuộc tính biến
        thể khác nhau
        """
        if 'variants' in data:
            variants = list()
            hash_map = dict()
            for variant in data['variants']:
                attrs = variant['attributes']
                attrs.sort(key=lambda x: x['id'])  # sort attributes by id

                if len(variants) > 0:
                    prev_variant = variants[-1]
                    if len(prev_variant) != len(attrs):
                        raise exc.BadRequestException(
                            '2 biến thể có các thuộc tính biến thể khác nhau')
                    for a, b in zip(prev_variant, attrs):
                        if a['id'] != b['id']:
                            raise exc.BadRequestException(
                                '2 biến thể có các thuộc tính biến thể khác nhau')

                str_attrs = str(attrs)
                if str_attrs in hash_map:
                    raise exc.BadRequestException('Tồn tại biến thể trùng lặp')
                hash_map[str_attrs] = 1
                variants.append(attrs)

    @classmethod
    def validate_variant_data(cls, data, seller_id, created_by, **kwargs):
        # Get variation attributes from product
        emails = list(map(lambda x: x.email, models.IAMUser.query.filter(
            models.IAMUser.seller_id == seller_id
        )))
        if kwargs.get('default_category'):
            seller_id = get_default_platform_owner_of_seller(seller_id)
        product = models.Product.query.join(
            models.ProductCategory,
            models.Product.id == models.ProductCategory.product_id
        ).join(
            models.Category,
            models.ProductCategory.category_id == models.Category.id
        ).filter(
            models.Product.id == data['product_id'],
            or_(
                models.Product.created_by == created_by,
                and_(
                    models.Product.editing_status_code != 'draft',
                    models.Product.created_by.in_(emails)
                ),
                and_(
                    models.Product.editing_status_code == 'active',
                    not_(models.Product.created_by.in_(emails))
                )
            )
        ).first()
        if not product:
            raise exc.BadRequestException(
                'Sản phẩm không tồn tại trên hệ thống')
        n_variants = models.ProductVariant.query.filter(
            models.ProductVariant.product_id == product.id
        ).first()
        if product.is_bundle and n_variants:
            raise exc.BadRequestException('Sản phẩm bundle không được phép tạo nhiều hơn 1 biến thể')
        if not product.category.is_active:
            raise exc.BadRequestException(
                'Danh mục ngành hàng đang vô hiệu, không thể tạo biến thể')
        if not product.category.is_leaf:
            raise exc.BadRequestException('Danh mục ngành hàng phải là lá')
        attribute_groups = product.attribute_set.groups
        group_ids = list(map(lambda group: group.id, attribute_groups))
        attr_group_attr = models.AttributeGroupAttribute.query.filter(
            models.AttributeGroupAttribute.attribute_group_id.in_(group_ids),
            models.AttributeGroupAttribute.is_variation,
        ).all()

        # nếu attribute set không có thuộc tính biến thể, tự động tạo biến thể mặc định
        if len(attr_group_attr) == 0:
            if 'variants' in data:
                raise exc.BadRequestException(
                    'Sản phẩm không có thuộc tính xác định biến thể biến thể')
            variant = models.ProductVariant.query.filter(
                models.ProductVariant.product_id == product.id,
            ).first()
            if variant:
                raise exc.BadRequestException(
                    'Sản phẩm đã tồn tại biến thể mặc định')
            return

        attr_map = dict()
        for item in attr_group_attr:
            attr_map[item.attribute_id] = item.attribute

        # Sản phẩm phải có biến thể
        if not bool(data.get('variants')):
            raise exc.BadRequestException('Sản phẩm bắt buộc phải có biến thể')
        cls._validate_variant_data_attribute(data, attr_map)

        variants = load_all_variant_attributes(product.id)

        attribute_ratio = models.Attribute.query.filter(
            models.Attribute.code == constants.UOM_RATIO_CODE_ATTRIBUTE).first()
        attribute_uom = models.Attribute.query.filter(models.Attribute.code == constants.UOM_CODE_ATTRIBUTE).first()
        cls._validate_attributes_variant_input(data, variants, attribute_ratio, attribute_uom)
        for variant_data in data['variants']:
            cls._validate_attributes_variant(attr_map, variant_data['attributes'], attribute_ratio)
            cls._validate_duplicate_variant(variant_data['attributes'], variants)

        return attr_map

    @classmethod
    def _validate_variant_data_attribute(cls, data, attr_map):
        pass

    @classmethod
    def _validate_attributes_variant_input(cls, data, variants, attribute_ratio, attribute_uom):
        def __init_exclude_attributes(exclude_uom):
            exclude_attribute_ids = [attribute_ratio.id]
            if exclude_uom:
                exclude_attribute_ids.append(attribute_uom.id)
            return exclude_attribute_ids

        def __is_variant_attribute(attribute_id):
            for variant in data['variants']:
                attributes = variant['attributes']
                for attr in attributes:
                    if attribute_id == attr['id']:
                        return True
            return False

        def __build_old_map_variants(exclude_uom):
            exclude_attribute_ids = __init_exclude_attributes(exclude_uom)
            response = {}
            for _, map_attributes in variants.items():
                attributes = []
                exclude_attributes = []
                for attribute_id, value in map_attributes.items():
                    if not __is_variant_attribute(attribute_id):
                        continue
                    f_value = safe_cast(value, float)
                    i_value = safe_cast(value, int)
                    value = f_value
                    if f_value == i_value:
                        value = i_value
                    item = {
                        'id': attribute_id,
                        'value': value
                    }
                    if attribute_id in exclude_attribute_ids:
                        exclude_attributes.append(item)
                    else:
                        attributes.append(item)
                attributes.sort(key=lambda x: x['id'])
                key = str(attributes)
                values = response.get(key, [])
                values.extend(exclude_attributes)
                response[key] = values

            return response

        def _map_attributes(exclude_uom):
            map_attributes = __build_old_map_variants(exclude_uom)
            exclude_attribute_ids = __init_exclude_attributes(exclude_uom)
            for variant in data['variants']:
                attributes = variant['attributes']
                include_attributes = list(filter(lambda x: x['id'] not in exclude_attribute_ids, attributes))
                exclude_attributes = list(filter(lambda x: x['id'] in exclude_attribute_ids, attributes))
                include_attributes.sort(key=lambda x: x['id'])
                key = str(include_attributes)
                values = map_attributes.get(key, [])
                values.extend(exclude_attributes)
                map_attributes[key] = values
            return map_attributes

        map_attributes_no_uom_and_ratio = _map_attributes(True)
        map_attributes_no_ratio = _map_attributes(False)
        for _, uom_and_ratio_values in map_attributes_no_uom_and_ratio.items():
            count_base = sum(1 for x in uom_and_ratio_values if safe_cast(x['value'], float) ==
                             1.0 and x['id'] == attribute_ratio.id)
            if count_base == 0:
                count_ratio = sum(1 for x in uom_and_ratio_values if x['id'] == attribute_ratio.id)
                if count_ratio > 0:
                    raise exc.BadRequestException('Vui lòng nhập thông tin đơn vị tính cơ sở')
            if count_base > 1:
                raise exc.BadRequestException('Đã tồn tại biến thể có đơn vị tính cơ sở với ratio=1')

        for _, ratio_values in map_attributes_no_ratio.items():
            count_non_base = sum(1 for x in ratio_values if safe_cast(x['value'], float) != 1.0)
            if count_non_base > 1:
                raise exc.BadRequestException('Đã tồn tại biến thể cùng loại có cùng đơn vị tính')

    @classmethod
    def _validate_attributes_variant(cls, attr_map, attributes_data, attribute_ratio):
        attr_visited = dict()
        for attribute_data in attributes_data:
            if attribute_data['id'] in attr_visited:
                raise exc.BadRequestException('Trùng lặp dữ liệu')
            if attribute_data['id'] not in attr_map:
                raise exc.BadRequestException('Thuộc tính không phải là thuộc tính biến thể')
            if not attr_map.get(attribute_data['id']) or attr_map.get(
                    attribute_data['id']).code != attribute_ratio.code:
                option = models.AttributeOption.query.get(attribute_data['value'])
                if not option:
                    raise exc.BadRequestException('Giá trị không tồn tại trên hệ thống')
                if option.attribute_id != attribute_data['id']:
                    raise exc.BadRequestException('Giá trị không thể gán cho thuộc tính')
            attr_visited[attribute_data['id']] = 1

    @classmethod
    def _validate_duplicate_variant(cls, attributes_data, variants):
        """Kiểm tra trùng lặp biến thể đã có trong database
        So sánh data truyền lên với toàn bộ các biến thể có trong database

        :param attributes_data: list of attrbiute-value, dữ liệu biến thể truyền lên trong request
        :param variants: các biến thể đã tồn tại trên database
        """

        def _is_dupplicated(attributes, attributes_data):
            duplicated = True
            for attribute_data in attributes_data:
                value = attributes.get(attribute_data['id'])
                if value is None:
                    duplicated = False
                    break
                if value != str(attribute_data['value']):
                    duplicated = False
                    break
            return duplicated

        for _, attributes in variants.items():
            duplicated = _is_dupplicated(attributes, attributes_data)
            if duplicated:
                raise exc.BadRequestException('Biến thể đã tồn tại trên hệ thống')


class CreateVariantValidatorFromImport(CreateVariantValidator):
    @classmethod
    def _validate_variant_data_attribute(cls, data, attr_map):
        data_attributes = data['variants'][0]['attributes']
        cls._validate_variant_uom_attribute(data_attributes, attr_map)

        missing_attr_ids = set(attr_map) - set(x['id'] for x in data_attributes)

        missing_attribute_names = ', '.join([attr_map[k].get('display_name') for k in missing_attr_ids])

        sellable_product = models.SellableProduct.query.filter(
            models.SellableProduct.product_id == data['product_id']
        ).first()

        seller_sku = sellable_product.seller_sku if sellable_product else ''

        if len(attr_map) > len(data_attributes):
            raise exc.BadRequestException(
                f'Vui lòng cập nhật thông tin biến thể {missing_attribute_names} cho SKU {seller_sku}')

    @classmethod
    def _validate_variant_uom_attribute(cls, data, attr_map):
        uom_attr = None
        for _, attr in attr_map.items():
            if attr.code == constants.UOM_CODE_ATTRIBUTE:
                uom_attr = attr
                break

        if uom_attr and not any(d.get('id') == uom_attr.id for d in data):
            raise exc.BadRequestException(
                'Đơn vị tính không đúng. Vui lòng nhập chính xác thông tin (xem ở Dữ liệu mẫu)')


class CreateImageValidator(Validator):
    @classmethod
    def _validate_get_image(cls, image_url: str, **kwargs):
        try:
            from catalog.biz.product_import.images import download_from_internet
            response = download_from_internet(image_url, verify=kwargs.get('verify', True))


            if response.status_code != 200:
                raise exc.BadRequestException('Hệ thống đang gặp lỗi. Vui lòng thử lại sau')

            return response
        except requests.exceptions.MissingSchema:
            raise exc.BadRequestException('Đường dẫn không hợp lệ')
        except requests.exceptions.RequestException:
            raise exc.BadRequestException('Hệ thống đang gặp lỗi. Vui lòng thử lại sau')

    @staticmethod
    def validate_image(data, is_advance_validation=True, **kwargs):
        _DEFAULT_MAX_IMAGE_SIZE = 2 * 1024 * 1024
        responses = []
        for variant in data.get('variants'):
            if variant.get('images'):
                if len(variant.get('images')) > 36:
                    raise exc.BadRequestException('Vượt quá giới hạn ảnh cho một biến thế (36 ảnh)')
                for image in variant.get('images'):
                    url = image.get('url', '')
                    if kwargs.get('allow_all_urls', False) or url.startswith(config.BASE_IMAGE_URL):
                        if is_advance_validation:
                            response = UpdateVariantValidator._validate_get_image(url, **kwargs)
                            if not response.headers.get('Content-Type') in ['image/jpeg', 'image/png']:
                                raise exc.BadRequestException('Ảnh không đúng định dạng')

                            if int(response.headers.get('Content-Length')) > _DEFAULT_MAX_IMAGE_SIZE:
                                raise exc.BadRequestException('Ảnh không được vượt quá 2MB')

                            responses.append(response)
                    else:
                        raise exc.BadRequestException('Đường dẫn không hợp lệ')
        if is_advance_validation:
            return responses


class UpdateVariantValidator(CreateImageValidator):
    @staticmethod
    def validate_id(data, **kwargs):
        if len(data.get('variants')) == 0:
            raise exc.BadRequestException('Bạn cần cập nhật một thông tin nào đó')

        list_variant_ids = []
        for item in data.get('variants'):
            list_variant_ids.append(item.get('id'))

        list_product_variants = models.ProductVariant.query.filter(
            models.ProductVariant.id.in_(list_variant_ids)
        ).all()

        if len(list_variant_ids) != len(list_product_variants):
            raise exc.BadRequestException('Biến thể không chính xác')

        product_id = None
        for product_variant in list_product_variants:
            if not product_id:
                product_id = product_variant.product_id
            elif product_variant.product_id != product_id:
                raise exc.BadRequestException('Các biến thể không thuộc cùng 1 sản phẩm')

class UpdateVariantValidatorWithoutCheckImage(UpdateVariantValidator):
    @staticmethod
    def validate_image(data, **kwargs):
        CreateImageValidator.validate_image(data, is_advance_validation=False, **kwargs)

class UpsertExternalVariantImagesValidator(UpdateVariantValidator):
    @staticmethod
    def validate_image(data, **kwargs):
        for variant in data.get('variants'):
            if len(variant.get('images')) > 36:
                raise exc.BadRequestException('Vượt quá giới hạn ảnh cho một biến thế (36 ảnh)')


class CreateVariantAttributeValidator(Validator):
    @classmethod
    def _validate_variants_belong_togather_product(cls, variant_ids, seller_id):
        """Kiểm tra các variant phải tồn tại, cùng thuộc một sản phẩm và phải
        đủ số lượng variant

        :param variant_ids: list[int]
        :return: list[m.ProductVariant]
        """
        seller = seller_service.get_seller_by_id(seller_id)
        if not seller:
            raise exc.BadRequestException('User không thuộc seller nào')
        variants = list()
        for variant_id in variant_ids:
            variant = models.ProductVariant.query.get(variant_id)
            if not variant:
                raise exc.BadRequestException('Tồn tại biến thể không hợp lệ')
            if variants and variants[-1].product_id != variant.product_id:
                raise exc.BadRequestException('Các biến thể phải cùng một sản phẩm')
            variants.append(variant)
        return variants

    @classmethod
    def _validate_data_type(cls, dtype, value):
        """Kiểm tra kiểu dữ liệu giá trị các thuộc tính truyền lên phải khớp
        với value_type của thuộc tính

        :param dtype: str, value_type of models.Attribute
        :param value: Union[str, int, float, list[int]], attribute value in request
        :return: None
        """
        if dtype == 'text':
            if not isinstance(value, str):
                raise exc.BadRequestException('Dữ liệu phải là text')
            if len(value) > 255:
                raise exc.BadRequestException('Giá trị text quá dài')
        elif dtype == 'number':
            if not (isinstance(value, int) or isinstance(value, float)):
                raise exc.BadRequestException('Dữ liệu phải là kiểu số')
        elif dtype == 'selection':
            if not isinstance(value, int):
                raise exc.BadRequestException('Giá trị phải là option id')
        else:
            if not isinstance(value, list):
                raise exc.BadRequestException('Giá trị phải là danh sách các option id')

    @classmethod
    def _validate_variant(cls, variant_data, attribute_metadata):
        """_validate_variant

        :param variant_data: dict
        :param attribute_metadata: dict
        :return: dict
        """
        cls._validate_attribute_not_belong_attribute_set(
            variant_data['attributes'], attribute_metadata)
        attr_data_hash_map = {
            data['id']: data
            for data in variant_data['attributes']
        }
        for meta_id, metadata in attribute_metadata.items():
            data = attr_data_hash_map.get(meta_id, None)

            if metadata['is_variation'] and data is not None:
                raise exc.BadRequestException('Không điền giá trị thuộc tính dùng để xác định biến thể')
            if data is None or data['value'] is None:
                continue

            if metadata['is_unsigned']:
                try:
                    v = float(data['value'])
                except ValueError:
                    raise exc.BadRequestException(
                        'Giá trị thuộc tính {} phải là số'.format(metadata.get('name'))
                    )
                else:
                    if v <= 0:
                        raise exc.BadRequestException(
                            'Giá trị thuộc tính {} phải lớn lớn hơn 0'.format(metadata.get('name')))

            cls._validate_data_type(metadata['value_type'], data['value'])

            if metadata['value_type'] in ('selection', 'multiple_select'):
                option_ids = [data['value']] if isinstance(data['value'], int) \
                    else data['value']
                n_options = models.AttributeOption.query.filter(
                    models.AttributeOption.id.in_(option_ids),
                    models.AttributeOption.attribute_id == meta_id
                ).count()
                if n_options < len(option_ids):
                    raise exc.BadRequestException(
                        'Tồn tại giá trị không hợp lệ'
                    )
        return variant_data

    @classmethod
    def _validate_attribute_not_belong_attribute_set(cls, attributes_data, attributes_metadata):
        """Kiểm tra tất cả các attribute truyền lên phải cùng thuộc attribute set và là unique trong request

        :param attributes_data:
        :param attributes_metadata:
        """
        attr_visited = dict()
        for attribute_data in attributes_data:
            if attribute_data['id'] in attr_visited:
                raise exc.BadRequestException('Tồn tại dữ liệu trùng lặp')
            attr_visited[attribute_data['id']] = 1

    @classmethod
    def _load_metadata(cls, attribute_set_id):
        attributes = dict()
        attribute_groups = models.AttributeGroup.query.filter(
            models.AttributeGroup.attribute_set_id == attribute_set_id).all()
        for group in attribute_groups:
            attribute_group_attributes = models.AttributeGroupAttribute.query.filter(
                models.AttributeGroupAttribute.attribute_group_id == group.id).all()
            for attribute_group_attribute in attribute_group_attributes:
                attributes[attribute_group_attribute.attribute.id] = {
                    'id': attribute_group_attribute.attribute.id,
                    'code': attribute_group_attribute.attribute.code,
                    'name': attribute_group_attribute.attribute.name,
                    'value_type': attribute_group_attribute.attribute.value_type,
                    'is_system': group.system_group,
                    'is_variation': attribute_group_attribute.is_variation,
                    'is_unsigned': attribute_group_attribute.attribute.is_unsigned
                }
        return attributes

    @classmethod
    def validate_data(cls, data, seller_id, **kwargs):
        """Kiểm tra dữ liệu

        :param data: dict
        :param **kwargs:
        """
        variant_ids = list(map(
            lambda variant_data: variant_data['id'],
            data['variants']
        ))
        variants = cls._validate_variants_belong_togather_product(variant_ids, seller_id)
        product = variants[0].product
        if product.master_category:
            if not product.master_category.is_leaf:
                raise exc.BadRequestException('Danh mục của sản phẩm không phải danh mục lá')
            if not product.master_category.is_active:
                raise exc.BadRequestException('Danh mục của sản phẩm đang vô hiệu')
        # load attribute set detail, include system group
        attribute_metadata = cls._load_metadata(product.attribute_set_id)
        for variant_data in data['variants']:
            cls._validate_variant(variant_data, attribute_metadata)

        return data


class GetListVariantValidator(Validator):
    @staticmethod
    def validate_product_id(product_id=None, **kwargs):
        if not product_id:
            return
        product = models.Product.query.get(product_id)
        if not product:
            raise exc.BadRequestException(f'Không tồn tại sản phẩm có id là {product_id}')
        if product.editing_status_code == 'draft' and product.created_by != current_user.email:
            raise exc.BadRequestException(f'Không tồn tại sản phẩm có id là {product_id}')


class GetListVariantAttributeListValidator(Validator):
    @staticmethod
    def validate_variant_ids(variant_ids, **kwargs):
        variant_ids = set(variant_ids)
        n_variants = models.ProductVariant.query.filter(
            # or_(
            #     models.ProductVariant.created_by == current_user.email,
            #     and_(
            #         models.ProductVariant.created_by != current_user.email,
            #         models.ProductVariant.editing_status_code == 'approved'
            #     )
            # ),
            models.ProductVariant.id.in_(variant_ids)
        ).count()
        if len(variant_ids) > n_variants:
            raise exc.BadRequestException('Tồn tại id của một biến thể không tồn tại')
