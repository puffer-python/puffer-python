# coding=utf-8
import logging
from catalog.constants import UOM_CODE_ATTRIBUTE

from flask_login import current_user
from funcy import pluck_attr
from sqlalchemy import exists, and_, or_

from catalog.utils import safe_cast
from catalog import models as m
from catalog.extensions import exceptions as exc
from catalog.validators import Validator
from catalog.validators.products import ProductCommonValidator
from catalog.services import provider as provider_srv

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)

def _get_base_variant_id(variant_id):
    sample_variant = m.ProductVariant.query.get(variant_id)
    base_variant_id = 0
    all_uom_ratios = sample_variant.all_uom_ratios.split(',')
    if len(all_uom_ratios) <= 1:
        return -1
    for uom_ratio in all_uom_ratios:
        if safe_cast(uom_ratio.split(':')[1], float) == 1.0:
            base_variant_id = safe_cast(uom_ratio.split(':')[0], int)
            break
    
    base_uom_variant = m.VariantAttribute.query.join(
        m.Attribute,
        m.Attribute.id == m.VariantAttribute.attribute_id
    ).filter(
        m.VariantAttribute.variant_id == base_variant_id,
        m.Attribute.code == UOM_CODE_ATTRIBUTE
    ).first()
    return (base_uom_variant.variant_id, base_uom_variant.get_option_value())

def _get_base_variants(variant_ids):
    if len(variant_ids) == 0:
        return []
    base_uom_and_values = []
    for variant_id in variant_ids:
        result = _get_base_variant_id(variant_id)
        base_uom_and_values.append(result)
    return base_uom_and_values

def _validate_sellable_product_status(sellable, status):
    if status not in sellable.editing_status.can_moved_status.split(','):
        expect_status = m.EditingStatus.query.filter(m.EditingStatus.code == status).first()
        raise exc.BadRequestException(
            f'Không được chuyển trạng thái của sản phẩm {sellable.name} từ {sellable.editing_status.name} sang {expect_status.name}')
    if status in ('pending_approval', 'active'):
        if not bool(sellable.terminal_seo.description):
            raise exc.BadRequestException(
                message=f'Sản phẩm {sellable.name} thiếu mô tả đặc điểm chi tiết',
                errors={
                    'common': [{
                        'field': 'detailedDescription',
                        'message': 'Thiếu mô tả đặc điểm chi tiết'
                    }]
                }
            )
        image = m.VariantImage.query.filter(
            m.VariantImage.product_variant_id == sellable.variant_id,
            m.VariantImage.status.is_(True)
        ).first()
        if not image:
            raise exc.BadRequestException(
                f'Sản phẩm {sellable.name} cần có ít nhất 1 hình ảnh',
                {'images': []}
            )
        if status == 'active' and sellable.is_bundle:
            if len(sellable.children) == 0:
                raise exc.BadRequestException(
                    message='Bundle phải có ít nhất 1 sản phẩm con',
                    errors={'bundle': []}
                )
            for item in sellable.children:
                if item.editing_status_code != 'active':
                    raise exc.BadRequestException(
                        message=f'Bundle có sản phẩm con {item.name} là {item.editing_status.name}',
                        errors={'bundle': []}
                    )
    elif status == 'inactive':
        if bool(sellable.parents):
            raise exc.BadRequestException(
                f'SKU đang thuộc sản phẩm bundle {sellable.parents[0].name}. Vui lòng gỡ sku ra khỏi bundle trước khi vô hiệu')


class CreateSellableProductsValidator(Validator):
    @staticmethod
    def validate_able_to_create_sku(product_id, **kwargs):
        """

        :param product_id:
        :param kwargs:
        :return:
        """
        product = m.Product.query.get(product_id)
        if not product:
            raise exc.BadRequestException(
                message='Sản phẩm không tồn tại',
                errors={'productId': product_id}
            )

    @staticmethod
    def validate_the_uniqueness(sellable_products, **kwargs):
        unique_set = set()
        for sellable in sellable_products:
            if sellable.get('seller_sku'):
                # Validate with existed skus in DB
                variant = SellableProductValidator.validate_variant_id(
                    variant_id=sellable.get('variant_id'),
                    seller_sku=sellable.get('seller_sku'),
                    **kwargs
                )
                # Validate with skus in the payload
                unique_sku = (sellable.get('seller_sku'), variant.unit.code, variant.uom_ratio)
                if unique_sku in unique_set:
                    raise exc.BadRequestException(f"Sản phẩm {sellable.get('seller_sku')} đã tồn tại")
                unique_set.add(unique_sku)

    @staticmethod
    def validate_valid_variant_ids(product_id, sellable_products, **kwargs):
        """

        :param product_id:
        :param sellable_products:
        :param kwargs:
        :return:
        """
        if not bool(sellable_products):
            raise exc.BadRequestException(
                'Dữ liệu không được rỗng'
            )

        def is_valid_variant(product_id, variant_id):
            return m.db.session.query(
                exists().where(and_(
                    m.ProductVariant.id == variant_id,
                    m.ProductVariant.product_id == product_id
                ))
            ).scalar()

        variant_ids = [data['variant_id'] for data in sellable_products]
        if not all([is_valid_variant(product_id, variant_id)
                    for variant_id in variant_ids]):
            raise exc.BadRequestException(
                'Các biến thể phải thuộc cùng sản phẩm'
            )

        if len(set(variant_ids)) != len(variant_ids):
            raise exc.BadRequestException(
                'Không được phép tạo nhiều sku cho cùng một biến thể'
            )

    @staticmethod
    def validate_bundle_skus(product_id, sellable_products, **kwargs):
        """

        :param product_id:
        :param sellable_products:
        :param kwargs:
        :return:
        """
        product = m.Product.query.get(product_id)
        bundle_excl_fields = ('sku', 'barcode', 'part_number', 'manage_serial',
                              'auto_generate_serial')
        if product and product.is_bundle:
            err = []
            for sellable_data in sellable_products:
                err = err + [field for field in bundle_excl_fields
                             if field in sellable_data]

            if err:
                raise exc.BadRequestException(
                    'Receive unaccepted field(s) for bundle sku creation.',
                    errors=err
                )

    @staticmethod
    def validate_sellable_products_data(sellable_products, **kwargs):
        """

        :param sellable_products:
        :param kwargs:
        :return:
        """
        product = m.Product.query.get(kwargs.get('product_id'))
        cls = SellableProductValidator
        for product_data in sellable_products:
            cls.validate(product_data, product=product, seller_id=kwargs.get('seller_id'))

    @staticmethod
    def validate_shipping_type(sellable_products, **kwargs):
        for sellable_product in sellable_products:
            input_shipping_types = sellable_product.get('shipping_types')
            if input_shipping_types:
                db_shipping_types = m.ShippingType.query.filter(
                    m.ShippingType.id.in_(input_shipping_types),
                    m.ShippingType.is_active == 1
                ).all()
                if len(input_shipping_types) != len(db_shipping_types):
                    raise exc.BadRequestException('Shipping type không tồn tại hoặc đã bị vô hiệu')

    @staticmethod
    def validate_barcodes(sellable_products, **kwargs):
        seller_id = kwargs.get('seller_id')
        barcodes = []
        for data in sellable_products:
            if data.get('barcodes'):
                barcodes.extend(map(lambda x: x.get('barcode'), data.get('barcodes')))
        duplicate_dict = {b: barcodes.count(b) for b in barcodes}
        for barcode, count in duplicate_dict.items():
            if count > 1:
                raise exc.BadRequestException(
                    f'barcode {barcode} bị trùng lặp'
                )
        alias_sku = m.db.aliased(m.SellableProduct)
        alias_sku_barcode = m.db.aliased(m.SellableProductBarcode)

        duplicate_skus = m.db.session.query(
            alias_sku_barcode.barcode, alias_sku.seller_sku
        ).filter(
            alias_sku_barcode.barcode.in_(barcodes),
            alias_sku.id == alias_sku_barcode.sellable_product_id,
            alias_sku.seller_id == seller_id
        )
        if kwargs.get('sku'):
            duplicate_skus = duplicate_skus.filter(
                alias_sku.sku != kwargs.get('sku')
            )
        duplicate_skus = duplicate_skus.all()
        if duplicate_skus:
            duplicate_sku_barcodes_message = map(lambda x: '{} của SKU {}'.format(x.barcode, x.seller_sku),
                                                 duplicate_skus)
            raise exc.BadRequestException(f'barcode {str.join(",", duplicate_sku_barcodes_message)} đã tồn tại')


class SellableProductValidator(Validator):
    @staticmethod
    def validate_provider_id(provider_id=None, **kwargs):
        seller_id = kwargs.get('seller_id') or current_user.seller_id
        provider_id = provider_id or kwargs.get('seller_id') or seller_id
        if seller_id == provider_id:
            return True
        provider = provider_srv.get_provider_by_id(provider_id)
        if not provider or provider['sellerID'] != seller_id \
                or not provider['isActive']:
            raise exc.BadRequestException('Nhà cung cấp không hợp lệ')

    @staticmethod
    def validate_variant_id(variant_id, seller_sku=None, **kwargs):
        """
            - variant_id in int range(marshmallow)
            - variant_id must be existed in db
        :param variant_id:
        :param seller_sku:
        :param kwargs:
        :return:
        """
        seller = m.Seller.query.get(kwargs.get('seller_id'))  # type: m.Seller
        variant = m.ProductVariant.query.get(variant_id)
        if not variant:
            raise exc.BadRequestException(
                f'Biến thể có id {variant_id} không tồn tại'
            )
        existed = m.db.session.query(
            exists().where(and_(
                m.SellableProduct.seller_id == seller.id,
                m.SellableProduct.variant_id == variant_id
            ))
        ).scalar()
        if existed:
            raise exc.BadRequestException(
                f'Sản phẩm ứng với biến thể {variant_id} đã tồn tại'
            )

        if seller.manual_sku:
            uom_code = variant.unit.code
            uom_ratio = variant.uom_ratio
            existed_sku = m.SellableProduct.query.filter(
                m.SellableProduct.seller_id == seller.id,
                m.SellableProduct.seller_sku == seller_sku,
                m.SellableProduct.uom_code == uom_code,
                m.SellableProduct.uom_ratio == uom_ratio
            ).first()
            if existed_sku:
                raise exc.BadRequestException(f'Sản phẩm {seller_sku} đã tồn tại')
        return variant

    @staticmethod
    def validate_sku(product, sku=None, seller_sku=None, **kwargs):
        """
            - sku is required (marshmallow)
            - max 20 characters allowed (marshmallow)
            - only a-zA-Z0-9.-_ (marshmallow)
            - sku is unique to each seller
            - check whether auto generate sku is enabled
        :param product:
        :param sku:
        :param kwargs:
        :return:
        """
        seller_id = kwargs.get('seller_id') or current_user.seller_id
        seller = m.Seller.query.get(seller_id)  # type: m.Seller
        if not seller.manual_sku:
            if seller_sku not in (None, ''):
                raise exc.BadRequestException('SKU được cấu hình tự động')
        else:
            if not sku and not seller_sku and not product.is_bundle:
                raise exc.BadRequestException('Vui lòng bổ sung Mã sản phẩm')

    @staticmethod
    def validate_barcode(barcode=None, obj_id=None, **kwargs):
        """
            - max 30 characters allowed (marshmallow)
            - only a-zA-Z0-9.- and space allowed (marshmallow)
            - barcode is unique to each seller
        :param barcode:
        :param obj_id:
        :param kwargs:
        :return:
        """
        if barcode:
            if obj_id:
                sellable = m.SellableProduct.query.get(obj_id)
                if sellable and sellable.barcode == barcode:
                    return
            seller_id = kwargs.get('seller_id') or current_user.seller_id
            existed = m.db.session.query(
                exists().where(and_(
                    m.SellableProduct.seller_id == seller_id,
                    m.SellableProduct.barcode == barcode,
                    m.SellableProduct.editing_status_code != 'inactive'
                ))
            ).scalar()
            if existed:
                raise exc.BadRequestException('Barcode đã tồn tại')

    @staticmethod
    def validate_supplier_sale_price(product, supplier_sale_price=None, **kwargs):
        """
            - integer, max 10 digits allowed (marshmallow)
            - check whether seller is using price management module
        :param product:
        :param supplier_sale_price:
        :param kwargs:
        :return:
        """
        if product.is_bundle:
            if supplier_sale_price:
                raise exc.BadRequestException(
                    'Receive unaccepted field for bundle SKU: supplierSalePrice'
                )
        seller_id = kwargs.get('seller_id') or current_user.seller_id
        seller = m.Seller.query.get(seller_id)  # type: m.Seller
        if not seller.is_manage_price:
            if supplier_sale_price is not None:
                raise exc.BadRequestException(
                    'Seller đang sử dụng module quản lý giá'
                )

    @staticmethod
    def validate_generate_serial(product, manage_serial=None,
                                 auto_generate_serial=None, **kwargs):
        """

        :param product:
        :param manage_serial:
        :param auto_generate_serial:
        :param kwargs:
        :return:
        """
        if not product.is_bundle:
            if manage_serial is None:
                raise exc.BadRequestException(
                    "Missing data for manage_serial field"
                )
            if auto_generate_serial is None:
                raise exc.BadRequestException(
                    "Missing data for auto_generate_serial field"
                )

        if not manage_serial and auto_generate_serial is True:
            raise exc.BadRequestException(
                'Seller không quản lý serial'
            )

    @staticmethod
    def validate_expiration(product, expiry_tracking=None, expiration_type=None,
                            days_before_exp_lock=None, **kwargs):
        """

        :param product:
        :param expiry_tracking:
        :param expiration_type:
        :param days_before_exp_lock:
        :param kwargs:
        :return:
        """
        if not product.is_bundle and expiry_tracking is None:
            raise exc.BadRequestException(
                'Missing data for expiry_tracking field'
            )
        elif product.is_bundle:
            if expiry_tracking:
                raise exc.BadRequestException(
                    'Receive unaccepted field for bundle SKU: expiryTracking'
                )
            if expiration_type:
                raise exc.BadRequestException(
                    'Receive unaccepted field for bundle SKU: expirationType'
                )
            if days_before_exp_lock is not None:
                raise exc.BadRequestException(
                    'Receive unaccepted field for bundle SKU: daysBeforeExpLock'
                )
        if expiry_tracking is True and not expiration_type:
            raise exc.BadRequestException(
                'Loại đơn vị hạn sử dụng là bắt buộc'
            )
        if expiry_tracking is True and days_before_exp_lock is None:
            raise exc.BadRequestException(
                'Ngày xuất kho tối thiểu là bắt buộc'
            )


class UpdateSellableProductTerminalValidator(Validator):
    @staticmethod
    def validate_seller_terminals(seller_terminals, **kwargs):
        """

        :param seller_terminals:
        :param kwargs:
        :return:
        """

        def _validate_apply_seller_id(seller_id):
            existed = m.db.session.query(
                exists().where(m.Seller.id == seller_id)
            ).scalar()
            if not existed:
                raise exc.BadRequestException(
                    'Seller không tồn tại'
                )

        apply_seller_ids = []
        for seller_terminal in seller_terminals:
            apply_seller_id = seller_terminal.get('apply_seller_id')
            if apply_seller_id in apply_seller_ids:
                raise exc.BadRequestException(
                    f'Duplicate record(s) with seller id {apply_seller_id}'
                )
            apply_seller_ids.append(apply_seller_id)
            _validate_apply_seller_id(apply_seller_id)

            for seller_terminal_code in seller_terminal.get('terminals'):
                terminal_codes = seller_terminal_code.get('terminal_codes')
                terminal_type = seller_terminal_code.get('terminal_type')
                if terminal_codes == 'all':
                    break
                if not isinstance(terminal_codes, list):
                    raise exc.BadRequestException(
                        'Mã điểm bán sai định dạng'
                    )
                if not terminal_codes:
                    raise exc.BadRequestException(
                        'terminalCodes: Field may not be null/empty',
                        errors={'terminalCodes': terminal_codes}
                    )
                for terminal_code in terminal_codes:
                    if not isinstance(terminal_code, str):
                        raise exc.BadRequestException(
                            'Mã điểm bán không hợp lệ'
                        )
                terminals = m.Terminal.query.filter(
                    m.Terminal.code.in_(terminal_codes)
                ).all()
                if terminals is None or sorted(pluck_attr('code', terminals)) != sorted(terminal_codes):
                    raise exc.BadRequestException(
                        'Điểm bán không hợp lệ hoặc không được phép bán'
                    )

                for terminal in terminals:
                    if terminal.seller_id != apply_seller_id:
                        raise exc.BadRequestException(
                            'Điểm bán không hợp lệ'
                        )
                    if not terminal.is_active:
                        raise exc.BadRequestException(
                            'Điểm bán đã bị vô hiệu'
                        )
                    if terminal_type and terminal.type != terminal_type:
                        raise exc.BadRequestException(
                            'Kênh bán không hợp lệ'
                        )

    @staticmethod
    def validate_skus(skus, **kwargs):
        if isinstance(skus, list) and skus:
            sellable_products = m.SellableProduct.query.filter(
                m.SellableProduct.sku.in_(skus),
                m.SellableProduct.seller_id == current_user.seller_id,
                m.SellableProduct.editing_status_code != 'inactive'
            ).all()
            if sellable_products and sorted(pluck_attr('sku', sellable_products)) == sorted(skus):
                return True
        raise exc.BadRequestException(
            'SKU không hợp lệ hoặc đã bị vô hiệu'
        )


class CreateSellableProductsFromImportValidator(CreateSellableProductsValidator):
    @staticmethod
    def validate_able_to_create_sku(product_id, **kwargs):
        return True


class UpdateEditingStatusValidator(Validator):
    @classmethod
    def validate_data(cls, status, seller_id, ids=[], skus=[], **kwargs):
        status_existed = m.db.session.query(
            m.db.exists().where(m.EditingStatus.code == status)
        ).scalar()
        if not status_existed:
            raise exc.BadRequestException(f'Trạng thái {status} không tồn tại')
        if not ids and not skus:
            raise exc.BadRequestException('Phải tồn tại ít nhất một sellable')
        sellables = m.SellableProduct.query.filter(
            m.SellableProduct.seller_id == seller_id,
            and_(
                or_(
                    m.SellableProduct.id.in_(ids),
                    m.SellableProduct.sku.in_(skus),
                )
            )
        )
        if max(len(ids), len(skus)) != sellables.count():
            raise exc.BadRequestException('Cập nhật trạng thái biên tập của sản phẩm không tồn tại trên hệ thống',
                                          errors={})
        error_messages = []
        for sellable in sellables:
            if sellable.editing_status_code != status:
                try:
                    _validate_sellable_product_status(sellable, status)
                except exc.BadRequestException as error_message:
                    error_messages.append(error_message.message)
        if error_messages:
            raise exc.BadRequestException(
                message='\n'.join(error_messages)
            )


class UpdateCommonValidator(Validator):
    def __init__(self, id_or_sku, is_sku=True):
        if is_sku:
            sellable = m.SellableProduct.query.filter(
                m.SellableProduct.sku == id_or_sku
            ).first()
        else:
            sellable = m.SellableProduct.query.filter(
                m.SellableProduct.id == id_or_sku
            ).first()
        if not sellable:
            raise exc.BadRequestException('Không tồn tại sản phẩm')
        self.sellable = sellable

    def validate(self, data, obj_id=None, **kwargs):
        for fn_name in dir(self):
            fn = getattr(self, fn_name)
            if callable(fn) and fn_name.startswith('validate_'):
                fn(**data, obj_id=obj_id, **kwargs)

        return data

    def validate_2_is_bundle_sellable(self, data, **kwargs):
        field_not_update = {'tax_in_code', 'tax_out_code', 'barcode',
                            'part_number', 'allow_selling_without_stock',
                            'expiry_tracking', 'expiration_type', 'days_before_exp_lock'}
        intersection = field_not_update.intersection(data.keys())
        if self.sellable.is_bundle and intersection:
            raise exc.BadRequestException(
                f'Không update các fields {", ".join(list(intersection))}')

    def validate_3_data(self, data, **kwargs):
        seller_id = kwargs.get('seller_id') or current_user.seller_id
        if not bool(data):
            raise exc.BadRequestException('Không có dữ liệu')
        if 'category_id' in data:
            ProductCommonValidator.validate_category(
                data['category_id'],
                seller_id=seller_id,
                default_category=kwargs.get('default_category', ''))
        if 'master_category_id' in data:
            ProductCommonValidator.validate_master_category_id(data['master_category_id'])
        if 'brand_id' in data:
            ProductCommonValidator.validate_brand(data['brand_id'])
        if 'type' in data:
            ProductCommonValidator.validate_type(data['type'])
        if 'tax_in_code' in data:
            ProductCommonValidator.validate_tax_in_code(data['tax_in_code'])
        if 'tax_out_code' in data:
            ProductCommonValidator.validate_tax_out_code(data['tax_out_code'])
        if 'unit_id' in data:
            ProductCommonValidator.validate_unit(data['unit_id'])
        if 'barcode' in data:
            if self.sellable.barcode != data['barcode']:
                SellableProductValidator.validate_barcode(
                    data['barcode'], seller_id=seller_id,
                )
        if 'provider_id' in data:
            SellableProductValidator.validate_provider_id(data['provider_id'], seller_id=seller_id)

        self._validate_generate_serial(
            data.get('manage_serial'),
            data.get('auto_generate_serial'),
        )
        self._validate_expiration(
            expiry_tracking=data.get('expiry_tracking'),
            expiration_type=data.get('expiration_type'),
            days_before_exp_lock=data.get('days_before_exp_lock'),
        )
        CreateSellableProductsValidator.validate_shipping_type(
            sellable_products=[data], seller_id=kwargs.get('seller_id')
        )

    def _validate_generate_serial(self, manage_serial, auto_generate_serial):
        sellable = self.sellable
        manage_serial = manage_serial or sellable.manage_serial
        auto_generate_serial = auto_generate_serial or sellable.auto_generate_serial

        if not manage_serial and auto_generate_serial is True:
            raise exc.BadRequestException(
                'Seller không quản lý serial'
            )

    def _validate_expiration(self, expiry_tracking=None, expiration_type=None,
                             days_before_exp_lock=None, **kwargs):
        """

        :param expiry_tracking:
        :param expiration_type:
        :param days_before_exp_lock:
        :param obj_id:
        :param kwargs:
        :return:
        """
        if expiry_tracking is None and expiration_type is None:
            return True
        sellable = self.sellable
        if sellable.expiry_tracking and (expiry_tracking is False or expiration_type != sellable.expiration_type):
            raise exc.BadRequestException(
                'Bạn không thể sửa từ Có sang Không quản lý hạn sử dụng hoặc cập nhập loại hạn sử dụng'
            )
        expiry_tracking = expiry_tracking or sellable.expiry_tracking
        expiration_type = expiration_type or sellable.expiration_type
        days_before_exp_lock = days_before_exp_lock or sellable.days_before_exp_lock

        if expiry_tracking is True and not expiration_type:
            raise exc.BadRequestException(
                'Loại đơn vị hạn sử dụng là bắt buộc'
            )
        if expiry_tracking is True and days_before_exp_lock is None:
            raise exc.BadRequestException(
                'Ngày xuất kho tối thiểu là bắt buộc'
            )

    def validate_barcodes(self, data, **kwargs):
        barcodes_with_source = data.get('barcodes')
        if not barcodes_with_source:
            return
        seller_id = kwargs.get('seller_id')
        if not seller_id and kwargs.get('trust_seller_id'):
            seller_id = self.sellable.seller_id
        CreateSellableProductsValidator.validate_barcodes([{'barcodes': barcodes_with_source}], seller_id=seller_id,
                                                          sku=self.sellable.sku)


class UpdateSkusProductValidator(Validator):
    @staticmethod
    def get_invalid_product(moving_sellable_products, target_model, target_brand_id):
        skus_of_invalid_models = []
        skus_of_invalid_brands = []
        is_invalid = False
        for sellable_product in moving_sellable_products:
            if sellable_product.model != target_model:
                skus_of_invalid_models.append(sellable_product.seller_sku)
                is_invalid = True

            if sellable_product.brand_id != target_brand_id:
                skus_of_invalid_brands.append(sellable_product.seller_sku)
                is_invalid = True

        return {
            "is_invalid": is_invalid,
            "skus_of_invalid_models": skus_of_invalid_models,
            "skus_of_invalid_brands": skus_of_invalid_brands,
        }

    @staticmethod
    def process_error_message_from_invalid_product(error_result):
        skus_of_invalid_models = error_result["skus_of_invalid_models"]
        skus_of_invalid_brands = error_result["skus_of_invalid_brands"]
        error_strings_array = []
        if skus_of_invalid_models:
            invalid_skus_string = ", ".join(skus_of_invalid_models)
            error_statement = f"Các skus có model không đồng nhất: {invalid_skus_string}"
            error_strings_array.append(error_statement)
        if skus_of_invalid_brands:
            invalid_skus_string = ", ".join(skus_of_invalid_brands)
            error_statement = f"Các skus có thương hiệu không đồng nhất: {invalid_skus_string}"
            error_strings_array.append(error_statement)

        return " \n".join(error_strings_array)

    # validate if variant that we want to move that is included all other related variant
    # (incase: base uom's one, we have to check all of variant that takes part in variant_ids)
    # @moving_base_variant_ids is moving base variation variant id
    @staticmethod
    def _validate_uom_based_variations(moving_variant_ids, moving_base_variant_ids):
        variants = m.ProductVariant.query.filter(
            m.ProductVariant.id.in_(moving_variant_ids)
        ).all()
        related_variant_ids = []
        for variant in variants:
            if variant.id not in moving_base_variant_ids:
                continue
            all_uom_ratios = variant.all_uom_ratios
            variant_id_ratios = all_uom_ratios.split(',')
            for variant_id_ratio in variant_id_ratios:
                if variant_id_ratio == '':
                    return related_variant_ids
                variant_id_and_ratio = variant_id_ratio.split(':')
                processed_variant_id = safe_cast(variant_id_and_ratio[0], int)
                if processed_variant_id:
                    related_variant_ids.append(processed_variant_id)
        related_variant_ids = list(set(related_variant_ids))
        missing_non_base_variant_ids = list(filter(lambda x: x not in moving_variant_ids, related_variant_ids))
        if missing_non_base_variant_ids:
            raise exc.BadRequestException('Không thể di chuyển biến thể đơn vị tính cơ sở mà không di chuyển các biến thể đơn vị khác')
  

    @staticmethod
    def _compare_moving_skus_attr_with_target_product(moving_variant_dict, target_variant_attr_dict):
        variation_attr_ids = []
        _target_variant_attr_dict = {}
        variation_attr_ids = []
        for variant_id in target_variant_attr_dict.keys():
            target_attr_dict = target_variant_attr_dict[variant_id]
            _target_variant_attr_dict[variant_id] = ()
            for attr_id in target_attr_dict.keys():
                if attr_id not in variation_attr_ids:
                    variation_attr_ids.append(attr_id)
                attr_value = target_attr_dict[attr_id]
                _target_variant_attr_dict[variant_id] += (attr_value, )

        for moving_variant_id in moving_variant_dict.keys():
            moving_attr_dict = moving_variant_dict[moving_variant_id]
            # whenever number of moving's attribute less than target's one, it's mean they have not enough attribute to satisfy
            if len(moving_attr_dict.keys()) < len(variation_attr_ids):
                sellable_product = m.SellableProduct.query.filter(m.SellableProduct.variant_id == moving_variant_id).first()
                raise exc.BadRequestException(f"SKU: {sellable_product.seller_sku} không di chuyển được vì các thuộc tính không phù hợp")
            is_missing_variation_attr_on_target_product = list(filter(lambda x: x not in moving_attr_dict.keys(), variation_attr_ids))
            if bool(is_missing_variation_attr_on_target_product):
                sellable_product = m.SellableProduct.query.filter(m.SellableProduct.variant_id == moving_variant_id).first()
                raise exc.BadRequestException(f"SKU: {sellable_product.seller_sku} không di chuyển được vì các thuộc tính không phù hợp")
            else:
                tuple_moving_attr = tuple()
                #build tuple according order attribute id of destination product
                for attribute_id in variation_attr_ids:
                    moving_attr_value = moving_attr_dict[attribute_id]
                    if not bool(moving_attr_value):
                        sellable_product = m.SellableProduct.query.filter(m.SellableProduct.variant_id == moving_variant_id).first()
                        raise exc.BadRequestException(f"Sku: {sellable_product.seller_sku} không di chuyển được vì các thuộc tính không phù hợp")
                    tuple_moving_attr += (moving_attr_value,)
                # check set attribute if is corresponding of target and moving sku
                for target_attr_id in _target_variant_attr_dict.keys():
                    if _target_variant_attr_dict[target_attr_id] == tuple_moving_attr:
                        sellable_product = m.SellableProduct.query.filter(m.SellableProduct.variant_id == moving_variant_id).first()
                        raise exc.BadRequestException(f"Thuộc tính biến thể của sku: {sellable_product.seller_sku} không thể di chuyển vì đã tồn tại biến thể tương tự ở sản phẩm mong muốn")


    # return 
    # (
    #   {
    #      <variant_id_1>: (<attribute_value>, <attribute_value>, <attribute_value>, ...)
    #      <variant_id_2>: (<attribute_value>, <attribute_value>, <attribute_value>, ...)
    #   },
    #   [target_variant_attribute_value, target_variant_attribute_value, ....]
    # )
    #
    @staticmethod
    def build_target_variant_attr_dict_and_get_variation_attribute(target_variant_attrs):
        target_variant_attr_dict = {}
        target_variant_attr_ids = []
        for target_variant_attr in target_variant_attrs:
            if target_variant_attr.attribute_id not in target_variant_attr_ids:
                target_variant_attr_ids.append(target_variant_attr.attribute_id)
            if target_variant_attr.variant_id in target_variant_attr_dict:
                target_variant_attr_dict[target_variant_attr.variant_id] += (target_variant_attr.value, )
            else:
                target_variant_attr_dict[target_variant_attr.variant_id] = (target_variant_attr.value,)
        return (target_variant_attr_dict, target_variant_attr_ids)


    # return
    # {
    #   <variant_id>: {
    #       <attribute_id>: <attribute_value>,
    #       ....
    #   },
    #   <variant_id>: {
    #       <attribute_id>: <attribute_value>,
    #       ....
    #   },
    # }
    @staticmethod
    def _build_variant_dict(moving_variant_attrs):
        moving_variant_dict = {}
        for moving_variant_attr in moving_variant_attrs:
            if moving_variant_attr.variant_id in moving_variant_dict.keys():
                if moving_variant_attr.attribute_id not in moving_variant_dict[moving_variant_attr.variant_id].keys():
                    moving_variant_dict[moving_variant_attr.variant_id][moving_variant_attr.attribute_id] = moving_variant_attr.value
            else:
                moving_variant_dict[moving_variant_attr.variant_id] = {moving_variant_attr.attribute_id: (moving_variant_attr.value)}
        return moving_variant_dict

    ###
    # this function will return a set of base uom of target_product_sku
    # beside that
    # it's will compare all attribute value of moving sku with target_product as below listed condition
    # 1. must same base uom
    # 2. validate moving with other related if you want to move base uom
    #    ex: if you have chiếc - thùng - thúng
    #           you want to move chiếc => you have to move thùng - thúng also
    # 3. must have same variation's attribute type of target product
    #    ex: target product have: Color - material - size
    #        moving sku must have these attribute in order to moving them to target product
    # 4. value of paring all attribute of target product must differ to moving's ones
    #    ex: target product: color: red, material: iron, size: L
    #        moving sku: color: red, meterial: iron and size: L 
    #           => we have to reject moving sku to target product
    #              however, if moving's color or other one if different with all variant's attribute of target product: ok let's move it
    ###
    @staticmethod
    def _validate_moving_target_variants(moving_skus, target_product_skus):
        target_variant_ids = map(lambda x: x.variant_id, target_product_skus)

        target_variant_attrs = m.VariantAttribute.query.join(
            m.AttributeGroupAttribute,
            m.AttributeGroupAttribute.attribute_id == m.VariantAttribute.attribute_id
        ).join(
            m.AttributeGroup,
            m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
        ).join(
            m.AttributeSet,
            m.AttributeSet.id == m.AttributeGroup.attribute_set_id
        ).filter(
            m.VariantAttribute.variant_id.in_(list(target_variant_ids)),
            m.AttributeGroupAttribute.is_variation == True,
            m.AttributeSet.id == target_product_skus[0].attribute_set_id
        ).order_by(
            m.VariantAttribute.id,
            m.VariantAttribute.attribute_id
        ).all()
        moving_variant_ids = list(map(lambda x: x.variant_id, moving_skus))
        moving_attr_set_ids = list(map(lambda x: x.attribute_set_id, moving_skus))
        already_base_uom_variant_ids = []
        #get base uom of target product aka first condition - must same base uom
        base_uom_target_product_variant = _get_base_variant_id(target_product_skus[0].variant_id)
        base_uom_moving_variants = _get_base_variants(moving_variant_ids)
        target_variant_attr_dict = __class__._build_variant_dict(target_variant_attrs)
        _, target_uom_value = base_uom_target_product_variant
        # compare base uom
        for base_uom_moving_variant in base_uom_moving_variants:
            moving_attr_id, moving_uom_value = base_uom_moving_variant
            already_base_uom_variant_ids.append(moving_attr_id)
            if target_uom_value != moving_uom_value:
                moving_sellable_product = m.SellableProduct.query.filter(
                    m.SellableProduct.variant_id == moving_attr_id
                ).first()
                error_statement = f"Khác đơn vị tính cơ sở: {target_uom_value} (đích) và {moving_uom_value} (sản phẩm di chuyển: {moving_sellable_product.seller_sku})"
                raise exc.BadRequestException(error_statement)
        # second condition - validate moving with other related if you want to move base uom
        __class__._validate_uom_based_variations(moving_variant_ids, already_base_uom_variant_ids)

        moving_variant_attr = m.VariantAttribute.query.join(
            m.AttributeGroupAttribute,
            m.AttributeGroupAttribute.attribute_id == m.VariantAttribute.attribute_id
        ).join(
            m.AttributeGroup,
            m.AttributeGroup.id == m.AttributeGroupAttribute.attribute_group_id
        ).join(
            m.AttributeSet,
            m.AttributeSet.id == m.AttributeGroup.attribute_set_id
        ).filter(
            m.VariantAttribute.variant_id.in_(moving_variant_ids),
            m.AttributeSet.id.in_(moving_attr_set_ids)
        ).order_by(
            m.VariantAttribute.id,
            m.VariantAttribute.attribute_id
        ).all()
        # bulding moving_variant_attr in order to compare moving attribute type with target's one
        moving_variant_dict = __class__._build_variant_dict(moving_variant_attr)
        __class__._compare_moving_skus_attr_with_target_product(moving_variant_dict=moving_variant_dict, target_variant_attr_dict=target_variant_attr_dict)

    @staticmethod
    def validate_params_move_skus_to_single_product(moving_skus, target_product_id, seller_id):
        skus_set = list(set(moving_skus))

        moving_product_skus = m.SellableProduct.query.filter(
            m.SellableProduct.sku.in_(skus_set),
            m.SellableProduct.seller_id == seller_id
        ).all()


        if len(moving_product_skus) != len(skus_set):
            raise exc.BadRequestException("Danh sách sku có sản phẩm không tồn tại")

        target_product = m.Product.query.filter(
            m.Product.id == target_product_id
        ).first()

        if not target_product:
            raise exc.BadRequestException("Sản phẩm bạn muốn gắn không tồn tại")

        target_product_skus = m.SellableProduct.query.filter(
            m.SellableProduct.product_id == target_product_id
        ).all()

        store_sellable_product = None
        if len(target_product_skus):
            store_sellable_product = target_product_skus[0]
            if store_sellable_product and store_sellable_product.seller_id != seller_id:
                raise exc.BadRequestException("Sản phẩm bạn muốn gắn không tồn tại")

            __class__._validate_moving_target_variants(moving_skus=moving_product_skus, target_product_skus=target_product_skus)
        else:
            raise exc.BadRequestException("Không được move đến sản phẩm rỗng")

        sample_model = store_sellable_product.model

        list_invalid_result = __class__.get_invalid_product(
            moving_product_skus, sample_model, target_product.brand_id)
        if list_invalid_result["is_invalid"]:
            error_statement = __class__.process_error_message_from_invalid_product(list_invalid_result)
            raise exc.BadRequestException(error_statement)

class UpdateItemBundleValidator(Validator):
    @staticmethod
    def validate_1_sellable_id(sellable_id, seller_id, **kwargs):
        sellable = m.SellableProduct.query.filter(
            m.SellableProduct.seller_id == seller_id,
            m.SellableProduct.id == sellable_id
        ).first()
        if not sellable:
            raise exc.BadRequestException('Sản phẩm không tồn tại')
        if not sellable.is_bundle:
            raise exc.BadRequestException('Sản phẩm không phải sản phẩm bundle')

    @staticmethod
    def validate_2_items(items, **kwargs):
        sellable = m.SellableProduct.query.get(kwargs.get('sellable_id'))
        if len(items) == 0 and sellable.editing_status_code == 'active':
            raise exc.BadRequestException('Phải tồn tại ít nhất một sản phẩm')
        ids = list(map(lambda x: x['id'], items))
        if len(set(ids)) < len(ids):
            raise exc.BadRequestException('Không được tồn tại 2 sản phẩm giống nhau')
        n_item = m.SellableProduct.query.filter(
            m.SellableProduct.id.in_(ids),
            m.SellableProduct.is_bundle.is_(False),
            m.SellableProduct.editing_status_code != 'inactive',
            m.SellableProduct.seller_id == sellable.seller_id
        ).count()
        if n_item != len(ids):
            raise exc.BadRequestException('Tồn tại sản phẩm không hợp lệ')


class GetItemsBundleValidator(Validator):
    @staticmethod
    def validate_sellable_id(sellable_id, **kwargs):
        sellable_product = m.SellableProduct.query.filter(
            m.SellableProduct.id == sellable_id
        ).first()

        if not sellable_product:
            raise exc.BadRequestException('Sản phẩm không tồn tại')

        if not sellable_product.is_bundle:
            raise exc.BadRequestException('Sản phẩm không phải là 1 bundle')


class BaseSEOInfoValidator(Validator):
    @staticmethod
    def validate_terminal_code(seller_id, terminal_codes=None, **kwargs):
        if terminal_codes is None:
            return

        if not isinstance(terminal_codes, list):
            terminal_codes = [terminal_codes]

        terminals = m.Terminal.query.filter(
            m.Terminal.code.in_(terminal_codes),
            m.Terminal.is_active == 1
        ).all()

        if len(terminals) != len(terminal_codes):
            raise exc.BadRequestException('Điểm bán không tồn tại')

        seller_terminals = m.SellerTerminal.query.filter(
            m.SellerTerminal.seller_id == seller_id,
            m.SellerTerminal.terminal_id.in_([terminal.id for terminal in terminals])
        ).all()

        if len(seller_terminals) != len(terminal_codes):
            raise exc.BadRequestException('Seller không được phép xem hoặc thêm thông tin SEO ở điểm bán này')


class SEOInfoValidatorById(BaseSEOInfoValidator):
    @staticmethod
    def validate_sellable_product_id(sellable_id, seller_id, **kwargs):
        sellable_product = m.SellableProduct.query.get(sellable_id)

        if not sellable_product or not sellable_product.product:
            raise exc.BadRequestException('Sản phẩm không tồn tại')

        if seller_id != sellable_product.seller_id:
            raise exc.BadRequestException('Sản phẩm không thuộc về seller')


class SEOInfoValidatorBySku(BaseSEOInfoValidator):
    @staticmethod
    def validate_sku(sku, seller_id, **kwargs):
        sellable_product = m.SellableProduct.query.filter(
            m.SellableProduct.sku == sku
        ).first()

        if not sellable_product or not sellable_product.product:
            raise exc.BadRequestException('Sản phẩm không tồn tại')

        if seller_id != sellable_product.seller_id:
            raise exc.BadRequestException('Sản phẩm không thuộc về seller')


class UpsertSellableProductTerminalGroup(Validator):
    @staticmethod
    def validate_terminal_groups(terminal_groups, **kwargs):
        active_terminal_groups = m.TerminalGroup.query.filter(
            m.TerminalGroup.code.in_(terminal_groups),
            m.TerminalGroup.is_active.is_(True),
            m.TerminalGroup.type == 'SELL'
        ).all()
        if len(terminal_groups) != len(active_terminal_groups):
            raise exc.BadRequestException('Nhóm điểm bán không tồn tại, đã bị vô hiệu hoặc có loại khác SELL')

        number_of_seller_terminal_groups = m.SellerTerminalGroup.query.filter(
            m.SellerTerminalGroup.terminal_group_id.in_(
                [terminal_group.id for terminal_group in active_terminal_groups]),
            m.SellerTerminalGroup.seller_id == current_user.seller_id
        ).count()

        if len(terminal_groups) != number_of_seller_terminal_groups:
            raise exc.BadRequestException('Tồn tại nhóm điểm bán mà seller không được phép bán')

    @staticmethod
    def validate_sellable_products(sellable_products, **kwargs):
        if not sellable_products:
            raise exc.BadRequestException(
                'Dữ liệu truyền lên không hợp lệ'
            )
        number_of_active_sellable_products = m.SellableProduct.query.filter(
            m.SellableProduct.id.in_(sellable_products),
            m.SellableProduct.seller_id == current_user.seller_id
        ).count()

        if number_of_active_sellable_products != len(sellable_products):
            raise exc.BadRequestException(
                'Sản phẩm không hợp lệ hoặc đã bị vô hiệu'
            )
