# coding=utf-8
# pylint: disable=abstract-class-instantiated

import logging
import os
import uuid
import pandas as pd
import requests
import config
import re

from pandas import DataFrame, ExcelWriter
from catalog import models as m
from catalog.utils import highlight_error
from .images import import_variant_images
from sqlalchemy import func
from marshmallow import ValidationError
from flask_login import current_user
from catalog.utils import convert_to_html_tag, keep_single_spaces
from catalog.constants import IMPORT, UOM_CODE_ATTRIBUTE, COLOR_ERROR_IMPORT
from catalog.validators import products as validators
from catalog.extensions import convert_int_field, convert_float_field, message_translate
from catalog.services.seller import get_default_platform_owner_of_seller
from catalog.services.products import ProductService, ProductVariantService
from catalog.validators.variant import CreateVariantValidator, CreateVariantValidatorFromImport
from catalog.services.attributes import get_or_new_option
from catalog.api.product.product import schema
from catalog.validators.sellable import (
    CreateSellableProductsFromImportValidator,
)
from catalog.extensions.exceptions import BadRequestException
from catalog.api.product.variant.schema import CreateVariantsBodyRequest
from catalog.services.products.sellable import (
    create_sellable_products,
)
from catalog.api.product.sellable.schema import (
    SellableProductsRequest,
)
from catalog.services.shipping_types.shipping_type import get_shipping_type_by_category_id, \
    get_shipping_type_id_by_list_name

__author__ = 'Kien.HT'

_logger = logging.getLogger(__name__)

service = ProductService.get_instance()


class Importer:
    BAD_REQUEST_VARIANT_MESSAGES = [
        'Đơn vị tính không đúng. Vui lòng nhập chính xác thông tin (xem ở Dữ liệu mẫu)',
        'Tỉ lệ quy đổi phải lớn hơn 0',
        'Tỉ lệ quy đổi không hợp lệ',
        'Biến thể chọn làm đơn vị lưu kho cần có tỉ lệ quy đổi bằng 1',
        'Biến thể chọn làm đơn vị lưu kho không tồn tại',
        'Không được phép cập nhật đơn vị tính của biến thể',
        'Cấu hình đơn vị tính không hợp lệ',
        'Cấu hình đơn vị tính lưu kho không hợp lệ',
        'Loại đơn vị hạn sử dụng là bắt buộc',
        'Ngày xuất kho tối thiểu là bắt buộc'
    ]
    attribute_set_id = None

    def _get_category(self, data):
        if self.process.type in IMPORT.IMPORT_WITH_DEFAULT_CATEGORY:
            default_platform_owner = get_default_platform_owner_of_seller(current_user.seller_id)
            seller_id = default_platform_owner
        else:
            seller_id = current_user.seller_id
        if self.category:
            return self.category
        code = data.get('category', '').split('=>').pop(0)
        self.category = m.Category.query.filter(
            m.Category.code == code,
            m.Category.is_active == 1,
            m.Category.seller_id == seller_id
        ).first()
        return self.category

    def _map_product_data(self, data):
        data_brand = keep_single_spaces(str(data.get('brand', ''))).lower()
        brand = m.Brand.query.filter(
            func.lower(m.Brand.name) == data_brand,
            m.Brand.is_active == 1
        ).first()

        product_type = m.Misc.query.filter(
            m.Misc.type == 'product_type',
            m.Misc.name == data.get('product type')
        ).first()

        category = self._get_category(data)

        tax_in = m.Tax.query.filter(
            m.Tax.label == data.get('vendor tax', '')
        ).first()

        # only get tax out value if it is passed in the import file
        tax_out = None
        if data.get('vat', None):
            tax_out = m.Tax.query.filter(
                m.Tax.label == data.get('vat', '')
            ).first()

        result = {
            'name': data.get('product name'),
            'categoryId': category.id if category else None,
            'attributeSetId': self.attribute_set_id,
            'brandId': brand.id if brand else None,
            'type': product_type.code if product_type else None,
            'taxInCode': tax_in.code if tax_in else '',
            'taxOutCode': tax_out.code if tax_out else '',
            'warrantyMonths': convert_int_field(data.get('warranty months')),
            'warrantyNote': data.get('warranty note'),
            'detailedDescription': convert_to_html_tag(data.get('description')),
            'description': convert_to_html_tag(data.get('short description')),
            'isBundle': False
        }

        if data.get('master category'):
            master_category = m.MasterCategory.query.filter(
                m.MasterCategory.code == data.get('master category', '').split('=>').pop(0)
            ).first()
            if master_category:
                result['masterCategoryId'] = master_category.id

        if data.get('model'):
            result['model'] = data.get('model')

        result = {k: v for k, v in result.items() if v is not None}

        return result

    def __init__(self, data, process, import_type):
        self.process = process
        self.row = data
        self.seller = m.Seller.query.get(process.seller_id)  # type: m.Seller
        self.import_type = import_type
        self.variant = None
        self.base_uom = None
        self.category = None

    def init_attributes(self):
        from catalog.services.attribute_sets import AttributeSetService
        as_service = AttributeSetService.get_instance()  # attribute set service
        self.attribute_set_id = self.process.attribute_set_id
        self.attribute_set = as_service.get_attribute_set(self.process.attribute_set_id)  # type: m.AttributeSet
        self.attributes = self.attribute_set.get_variation_attributes()
        self.specifications_attributes = self.attribute_set.get_specifications_attributes()
        if not self.row.get('attribute set'):
            self.attribute_set_str = "%s=>%s" % (self.attribute_set.id, self.attribute_set.name)

    def update_data(self):
        if self.import_type == 'cha' and len(self.attributes) == 0:
            raise BadRequestException('Sản phẩm không có thuộc tính xác định biến thể')
        data = self._map_product_data(self.row)
        data = schema.ProductCreateRequestBody().load(data)
        default_category = False
        if self.process.type in IMPORT.IMPORT_WITH_DEFAULT_CATEGORY:
            default_category = True
        validators.ProductCommonFromImportValidator.validate(data, default_category=default_category)
        data.update({'editing_status_code': 'processing'})
        product = service.create_product(data, self.process.created_by)
        self.product = product
        if not product.id:
            raise BadRequestException("Không thể tạo sản phẩm %s" % str(data))
        return product

    def create_variant(self):
        attrs = []
        input_data = {'productId': self.product.id}
        for attribute in self.attributes:
            value_attribute = self.get_value_attribute(
                self.row.get(
                    attribute.code
                ),
                attribute
            )
            if value_attribute is not None:
                attrs.append({
                    'id': attribute.id,
                    'value': value_attribute
                })
        if attrs:
            variant_data = {'attributes': attrs}
            if self.row.get('product name').strip():
                variant_data['name'] = self.row.get('product name')
            input_data['variants'] = [variant_data]

        rs_data = CreateVariantsBodyRequest().load(input_data)
        rs_data = CreateVariantValidator.format_data(rs_data)
        seller_id = current_user.seller_id
        if self.process.type in IMPORT.IMPORT_WITH_DEFAULT_CATEGORY:
            import_with_default_category = True
        CreateVariantValidatorFromImport.validate({
            'data': rs_data,
            'seller_id': seller_id,
            'created_by': current_user.email,
        }, default_category=import_with_default_category)
        variant_service = ProductVariantService.get_instance()
        variant = variant_service.create_variants(
            self.product.id,
            rs_data.get('variants'),
            self.process.created_by,
            auto_commit=True
        )

        if len(variant) > 0:
            self.variant = m.ProductVariant.query.get(variant[0].get('id'))
        return self.variant

    def create_sku(self, sellable_create_signal=True):
        sellable_products = []

        data_variant = {
            'variantId': self.variant.id,
            'partNumber': self.row.get('part number', ''),
        }
        if self.row.notna().get('barcode') and self.row.get('barcode') != '<NA>':
            data_variant['barcode'] = ''
            barcode_with_commas = str(self.row.get('barcode'))
            barcodes = barcode_with_commas.split(',')
            barcodes_with_sources = []
            for barcode in barcodes:
                barcode = barcode.strip()
                if barcode:
                    data_variant['barcode'] = barcode
                    barcodes_with_sources.append({'barcode': barcode})
            data_variant['barcodes'] = barcodes_with_sources
        if self.row.get('seller_sku') and self.seller.manual_sku:
            data_variant['sellerSku'] = str(self.row.get('seller_sku'))
        if self.row.get('allow selling without stock?'):
            try:
                if self.row.get('allow selling without stock?').lower() == 'yes':
                    data_variant['allowSellingWithoutStock'] = True
                if self.row.get('allow selling without stock?').lower() == 'no':
                    data_variant['allowSellingWithoutStock'] = False
            except (TypeError, ValueError, AttributeError):
                pass

        if self.row.get('is tracking serial?'):
            try:
                if self.row.get('is tracking serial?').lower() == 'yes':
                    data_variant['manageSerial'] = True
                if self.row.get('is tracking serial?').lower() == 'no':
                    data_variant['manageSerial'] = False
            except (TypeError, ValueError, AttributeError):
                pass
        try:
            if self.row.get('expiry tracking', '').lower() == 'yes':
                data_variant['expiryTracking'] = True
            if self.row.get('expiry tracking', '').lower() == 'no':
                data_variant['expiryTracking'] = False
        except (TypeError, ValueError, AttributeError):
            pass
        if data_variant.get('expiryTracking') is True:
            if self.row.get('expiration type'):
                try:
                    if self.row.get('expiration type', '').lower() == 'ngày':
                        data_variant['expirationType'] = 1
                    if self.row.get('expiration type', '').lower() == 'tháng':
                        data_variant['expirationType'] = 2
                except (TypeError, ValueError, AttributeError):
                    pass
            if self.row.get('days before Exp lock'):
                try:
                    data_variant['daysBeforeExpLock'] = int(
                        self.row.get('days before Exp lock')
                    )
                except (TypeError, ValueError, AttributeError):
                    pass
        if self.row.get('shipping type'):
            data_variant['shippingTypes'] = get_shipping_type_id_by_list_name(self.row.get('shipping type', ))
        else:
            category = self._get_category(self.row)
            data_variant['shippingTypes'] = get_shipping_type_by_category_id(category.id)
        data_variant['shortDescription'] = str(self.row.get('short description')) if self.row.get(
            'short description') else None
        data_variant['description'] = str(self.row.get('description')) if self.row.get(
            'description') else None
        data_variant = {k: v for k, v in data_variant.items() if v is not None}
        sellable_products.append(data_variant)

        data = {
            'productId': self.product.id,
            'sellableProducts': sellable_products
        }
        data = SellableProductsRequest().load(data)
        data.update({'seller_id': current_user.seller_id})
        CreateSellableProductsFromImportValidator.validate(data)

        skus, message = create_sellable_products(data=data, sellable_create_signal=sellable_create_signal)
        if len(skus) > 0:
            self.sku = skus[0]

    def update_terminal(self):
        """
        Mapping sku with terminals where sellers is allowed to sell.
        Will skip terminals BadRequestException to keep Variant and Sku.
        Get all terminals group from Seller service
        """
        terminal_groups = self.process.terminal_groups

        if self.row.get('terminal_group', '').lower() == 'all':
            for terminal_group_code in terminal_groups:
                p_terminal_group = m.SellableProductTerminalGroup(
                    sellable_product_id=self.sku.id,
                    terminal_group_code=terminal_group_code,
                    created_by=current_user.email,
                    updated_by=current_user.email
                )
                m.db.session.add(p_terminal_group)
                m.db.session.commit()
            return

        if self.row.get('terminal_group', ''):
            for terminals_code in get_terminals_code(self.row.get('terminal_group', '')):
                for terminal_group_code in terminal_groups:
                    if terminals_code == terminal_group_code:
                        p_terminal_group = m.SellableProductTerminalGroup(
                            sellable_product_id=self.sku.id,
                            terminal_group_code=terminal_group_code,
                            created_by=current_user.email,
                            updated_by=current_user.email

                        )
                        m.db.session.add(p_terminal_group)
                        m.db.session.commit()

    def create_variant_images(self):
        image_urls = self.row.get('image urls', '')
        variant_id = self.variant.id
        import_variant_images.delay(
            variant_id=variant_id,
            urls=image_urls,
            email=current_user.email,
            send_environ=True
        )

    def import_variant_attributes(self):
        """
        :param variants:
        :param attributes:
        :param row:
        :type variant dict
        :return:
        """
        for attribute in self.specifications_attributes:
            value_attribute = self.get_value_attribute(
                keep_single_spaces(self.row.get(attribute.code)),
                attribute
            )
            if value_attribute:
                exists = m.VariantAttribute.query.filter(
                    m.VariantAttribute.variant_id == self.variant.id,
                    m.VariantAttribute.value == value_attribute,
                    m.VariantAttribute.attribute_id == attribute.id
                ).first()

                if exists is None:
                    variant_attribute_push_data = m.VariantAttribute(
                        variant_id=self.variant.id,
                        value=value_attribute,
                        attribute_id=attribute.id
                    )
                    m.db.session.add(variant_attribute_push_data)
                    m.db.session.commit()
        return None

    def get_value_attribute(self, value, attribute):
        """
        :type attribute m.Attribute
        :type: value str
        :param value:
        :param attribute:
        :return:
        """
        if attribute.code == UOM_CODE_ATTRIBUTE:
            value = keep_single_spaces(str(value))
        if not value or len(str(value)) > 255:
            return None
        if attribute.value_type == 'selection' and str(value):
            option = get_or_new_option(
                option_value=value,
                attribute_object=attribute
            )
            return option.id if option else None
        if attribute.value_type == 'multiple_select' and str(value):
            options = []
            for option_value in str(value).split(","):
                options.append(
                    get_or_new_option(
                        option_value=option_value,
                        attribute_object=attribute
                    )
                )
            return ','.join([str(option.id) for option in options]) if options else None
        if attribute.value_type == 'number':
            convert_value = None
            if attribute.is_float:
                convert_value = convert_float_field(value)
            if not attribute.is_float:
                convert_value = convert_int_field(value)
            if convert_value and convert_value <= 0 and attribute.is_unsigned:
                return None
            return convert_value
        if attribute.value_type == 'text':
            if len(str(value)) <= 255:
                return str(value)
        return None

    @message_translate.vn
    def import_row_don(self):
        """
                :type importer Importer
                :param importer:
                :return:
                """
        try:
            self.init_attributes()
            self.update_data()
            self.create_variant()
            self.import_variant_attributes()
            self.create_sku()
            self.create_variant_images()
        except (ValidationError, BadRequestException) as ex:
            if hasattr(self, 'product'):
                from catalog.services.products.product import delete_product
                delete_product(self.product.id)
            if hasattr(self, 'variant') and self.variant:
                from catalog.services.products.variant import delete_variant
                delete_variant(self.variant.id)
            if isinstance(ex, ValidationError):
                return dict(ex.messages)
            return ex.message
        except Exception as ex:
            _logger.exception(ex)
            if hasattr(self, 'product'):
                from catalog.services.products.product import delete_product
                delete_product(self.product.id)
            return "Hệ thống gặp lỗi"

    @message_translate.vn
    def import_row_cha(self):
        try:
            self.init_attributes()
            self.update_data()
            m.db.session.commit()
        except (ValidationError, BadRequestException) as ex:
            if isinstance(ex, ValidationError):
                return dict(ex.messages)
            return ex.message
        except Exception:
            m.db.session.rollback()
            return "Hệ thống gặp lỗi"

    @message_translate.vn
    def import_row_con(self):
        """
        """
        try:
            self.create_variant()
            self.import_variant_attributes()
            self.create_sku(sellable_create_signal=False)
            self.create_variant_images()

        except (ValidationError, BadRequestException) as ex:
            # variant map 1-1 with sku, just delete variant (don't need to delete sku)
            # because sku will not create when got Error + skip update_terminal errors
            if hasattr(self, 'variant') and self.variant:
                from catalog.services.products.variant import delete_variant
                # delete_variant(self.variant.id)
                if isinstance(ex, BadRequestException) and ex.message in self.BAD_REQUEST_VARIANT_MESSAGES \
                        or re.search("^Vui lòng cập nhật thông tin biến thể .+ cho SKU .*$", ex.message):
                    delete_variant(self.variant.id)
            if isinstance(ex, ValidationError):
                return dict(ex.messages)
            return ex.message
        except Exception as e:
            m.db.session.rollback()
            _logger.exception(e)
            return "Hệ thống gặp lỗi"


def get_terminals_code(data):
    if not isinstance(data, str):
        return []
    result = []
    for sub_str in data.split(','):
        result.append(sub_str.split('=>').pop(0))

    return result


def get_all_terminals(seller_id):
    from catalog.services.terminal import get_terminal_groups
    return [terminal_group.get('code') for terminal_group in get_terminal_groups(seller_id)]


def read_excel(path, header):
    df = pd.read_excel(
        path,
        header=header,
        keep_default_na=False,
    ).convert_dtypes()  # type: DataFrame
    return df.drop(0)


def save_excel(reader):
    # pylint: disable=abstract-class-instantiated
    tem_file = os.path.join(
        config.ROOT_DIR,
        'storage',
        '{}.xlsx'.format(uuid.uuid4())
    )

    with ExcelWriter(path=tem_file, engine='xlsxwriter',
                     options={'strings_to_urls': False}) as writer:  # pylint: disable=abstract-class-instantiated
        reader.style.apply(highlight_error, axis=1).to_excel(writer, index=False)

    file = open(tem_file, 'rb')
    send_file = {'file': (
        '{}.xlsx'.format(uuid.uuid4()),
        file.read(),
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )}
    r = requests.post('{}/upload/doc'.format(config.FILE_API),
                      files=send_file)
    os.remove(tem_file)
    if r.status_code == 200:
        return r.json().get('url')
    return None
