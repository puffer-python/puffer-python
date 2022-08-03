# coding=utf-8

from catalog import (
    validators,
)
from catalog.api.product.sku.product_schema import CreateProductRequest
from catalog.validators.category import CloneMasterCategory
from catalog.validators.products import ProductCommonValidator, GetProductInfoValidator
from catalog.validators.sellable import SellableProductValidator
from catalog.extensions import exceptions as exc


class UpsertProductValidator(validators.Validator):
    @staticmethod
    def validate_data(**data):
        UpsertProductValidator.__validate_product_format(**data)
        UpsertProductValidator.__validate_product_layer(**data)

    @staticmethod
    def __validate_product_format(**data):
        if not data.get('product_id'):
            CreateProductRequest().load_include_all(data)
            if not data.get('category_ids') and not data.get('category_id'):
                raise exc.BadRequestException('Vui lòng chọn danh mục ngành hàng')

    @staticmethod
    def __validate_product_layer(**data):
        if data.get('product_id'):
            GetProductInfoValidator.validate_product_id(**data)
        if data.get('seller_id'):
            CloneMasterCategory.validate_seller_id(**data)
        if data.get('provider_id'):
            SellableProductValidator.validate_provider_id(**data)
        if data.get('category_ids'):
            ProductCommonValidator.validate_categories(**data)
        if data.get('category_id'):
            ProductCommonValidator.validate_category(**data)
        if data.get('master_category_id'):
            ProductCommonValidator.validate_master_category_id(**data)
        if data.get('brand_id'):
            ProductCommonValidator.validate_brand(**data)
        if data.get('tax_in_code'):
            ProductCommonValidator.validate_tax_in_code(**data)
        if data.get('attribute_set_id'):
            ProductCommonValidator.validate_attribute_set_id(**data)
