# coding=utf-8

SQL_MAX_INTVAL = 4294967295  # TODO: remove, supplier_sale_price of sku more than it
BASE_UOM_RATIO = 1
FULLFILLMENT_BY_SELLER = 'FBS'
UOM_CODE_ATTRIBUTE = 'uom'
UOM_RATIO_CODE_ATTRIBUTE = 'uom_ratio'
PACK_CODE_ATTRIBUTES = ['pack_width', 'pack_length', 'pack_weight', 'pack_height']
DIMENSION_ATTRIBUTES_CODES = ['length', 'width', 'height', 'weight']
DEFAULT_MAX_LENGTH = 255
OPTION_VALUE_NOT_DISPLAY = 'KHT'
CATEGORY_MAX_DEPTH = 6
MAX_PAGE_SIZE_EXTERNAL_SERVICE_API = 1000
MAX_SUB_SKU = 10
SUB_SKU_POSTFIX = '_SUB_'
MAX_PAGE_SIZE_INTERNAL = 200
COLOR_ERROR_IMPORT = '#f4cccc'
MAX_RECORD = 10_000


class RAM_QUEUE:
    RAM_DEFAULT_PARENT_KEY = 'default'
    RAM_INSERT_CATEGORY_KEY = 'catalog.category.insert'
    RAM_UPDATE_CATEGORY_KEY = 'catalog.category.update'
    RAM_INSERT_BRAND_KEY = 'catalog.brand.insert'
    RAM_UPDATE_BRAND_KEY = 'catalog.brand.update'
    RAM_INSERT_UNIT_KEY = 'catalog.unit.insert'
    RAM_UPDATE_UNIT_KEY = 'catalog.unit.update'
    RAM_UPDATE_PRODUCT_DETAIL = 'sellable_product.update_product_detail'
    RAM_UPDATE_PRODUCT_DETAIL_V2 = 'sellable_product.update_product_detail_v2'
    RAM_PUSH_PRODUCT_DATA = 'sellable_product.push_data'
    RAM_UPDATE_ATTRIBUTE_KEY = 'catalog.attribute.update'
    RAM_PLATFORM_SELLER_UPSERT_KEY = 'catalog.platform_seller.upsert'


class ExportSellable:
    EXPORT_GENERAL_INFO = 1
    EXPORT_ALL_ATTRIBUTE = 2
    EXPORT_SEO_INFO = 3


class ATTRIBUTE_TYPE:
    SELECTION = 'selection'
    MULTIPLE_SELECT = 'multiple_select'
    NUMBER = 'number'
    TEXT = 'text'


class IMPORT:
    IMPORT_WITH_DEFAULT_CATEGORY = [
        'create_product_basic_info',
        'create_product',
        'update_product',
        'create_product_quickly'
    ]
