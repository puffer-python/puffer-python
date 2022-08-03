from catalog.validators.create_list_sku.product import UpsertProductValidator
from catalog.validators.create_list_sku.variant import UpsertVariantValidator
from catalog.validators.sellable import CreateSellableProductsValidator, UpdateCommonValidator, \
    UpdateEditingStatusValidator, UpdateSkusProductValidator
from catalog.validators.variant import CreateVariantAttributeValidator, UpdateVariantValidator
from catalog.extensions import exceptions as exc

from .variant_schema import CreateVariantRequest
from .sku_schema import CreateSkuRequest
import logging

_logger = logging.getLogger(__name__)


def __validate_product_format(product):
    UpsertProductValidator.validate(product)


def __validate_variant_format(variant):
    if not variant.get('variant_id'):
        CreateVariantRequest().load_include_all(variant)


def validate_variants_business(product_id, attribute_set_id, variants, common_data):
    return UpsertVariantValidator.validate(product_id, attribute_set_id, variants, common_data)


def validate_variant_attributes_business(data, seller_id):
    return CreateVariantAttributeValidator.validate({
        'data': data,
        'seller_id': seller_id
    })


def validate_variant_images_business(data):
    return UpdateVariantValidator.validate({
        'data': data,
    })


def __validate_sku_format(sku):
    if sku and not sku.get('sku'):
        CreateSkuRequest().load_include_all(sku)


def validate_update_sku_business(sku, data, seller_id=None):
    UpdateCommonValidator(sku).validate_barcodes(data, seller_id=seller_id, trust_seller_id=True, sku=sku)


def validate_move_sku_to_single_product(skus, seller_id, product_id):
    return UpdateSkusProductValidator.validate_params_move_skus_to_single_product(
        moving_skus=skus, seller_id=seller_id, target_product_id=product_id
    )


def __validate_barcodes(sellable_products):
    barcodes = []
    for data in sellable_products:
        if data.get('barcodes'):
            barcodes.extend(map(lambda x: x.get('barcode'), data.get('barcodes')))
    duplicate_dict = {b: barcodes.count(b) for b in barcodes}
    for barcode, count in duplicate_dict.items():
        if count > 1:
            raise exc.BadRequestException(f'barcode {barcode} bị trùng lặp')


def validate_skus_business(product_id, data_insert: list, data_update: list, seller_id):
    all_skus = []
    if data_update:
        for sku in data_update:
            if sku.get('sku'):
                UpdateCommonValidator(sku.get('sku')).validate({
                    'data': sku, 'seller_id': seller_id
                })
                if 'editing_status_code' in sku:
                    UpdateEditingStatusValidator.validate({
                        'seller_id': seller_id,
                        'skus': [sku.get('sku')],
                        'status': sku.get('editing_status_code')
                    })
                all_skus.append(sku)

    if data_insert:
        all_skus.extend(data_insert)
        CreateSellableProductsValidator.validate(
            {'product_id': product_id, 'sellable_products': data_insert, 'seller_id': seller_id}
        )
    __validate_barcodes(all_skus)


def validate_format(data):
    product_id = data.get('product_id')
    __validate_product_format(data)
    variants = data.get('variants') or []
    for variant in variants:
        variant_id = variant.get('variant_id')
        if not product_id and variant_id:
            raise exc.BadRequestException('Không có thông tin sản phẩm khi cập nhật biến thể')
        if not variant_id and (variant.get('sku') or {}).get('sku'):
            raise exc.BadRequestException('Không có thông tin biến thể khi cập nhật sku')
        __validate_variant_format(variant)
        __validate_sku_format(variant.get('sku'))
