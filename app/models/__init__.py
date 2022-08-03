# coding=utf-8
import logging

from .base import (
    TimestampMixin,
    init_app,
    db,
    migrate
)
from .tax import Tax
from .misc import Misc
from .amqp_message import AMQPMessage
from .attribute_option import AttributeOption
from .product import Product
from .product_variant import ProductVariant
from .sellable_product import SellableProduct
from .attribute import Attribute
from .variant_attribute import VariantAttribute
from .variant_image import VariantImage
from .product_detail import ProductDetail
from .product_attribute import ProductAttribute
from .attachment import Attachment
from .editing_status_history import EditingStatusHistory
from .editing_status import EditingStatus
from .product_status import (
    ProductStatus,
    ProductLabel
)
from .selling_status import SellingStatus
from .log import LogImportFile, LogEditProduct, LogEditProductConfigurable
from .color import Color
from .brand import Brand
from .unit import Unit
from .attribute_set import (
    AttributeSet,
    AttributeSetConfig,
    AttributeSetConfigDetail
)
from .attribute_group import AttributeGroup
from .attribute_description import AttributeDescription
from .attribute_group_attribute import AttributeGroupAttribute
from .sellable_product import SellableProduct
from .sellable_product_bundle import SellableProductBundle
from .sellable_product_terminal import SellableProductTerminal
from .category import Category
from .master_category import MasterCategory
from .terminal import Terminal
from .terminal_group import TerminalGroup
from .terminal_group_terminal import TerminalGroupTerminal
from .seller_terminal_group import SellerTerminalGroup
from .seller_terminal import SellerTerminal
from .seller import Seller
from .file import File
from .product_unit import ProductUnit
from .file_cloud import FileCloud
from .product_srm_request import ProductSrmRequest
from .message_log import MsgLog
from .srm_status import SRMStatus
from .action_log import ActionLog
from .file_import import FileImport
from .user import User
from .iam_user import IAMUser
from .sale_category import SaleCategory
from .provider import Provider
from .sellable_product_seo_info import SellableProductSeoInfo
from .sellable_product_seo_info_terminal import SellableProductSeoInfoTerminal
from .sellable_product_tag import SellableProductTag
from .product_log import ProductLog
from .shipping_policy import ShippingPolicy, ShippingPolicyMapping
from .sellable_product_terminal_group import SellableProductTerminalGroup
from .terminal_group import TerminalGroup
from .terminal_group_terminal import TerminalGroupTerminal
from .seller_terminal_group import SellerTerminalGroup
from .variant_image_log import VariantImageLog
from .failed_variant_image_request import FailedVariantImageRequest
from .result_import import ResultImport
from .shipping_type import ShippingType
from .sellable_product_shipping_type import SellableProductShippingType
from .category_shipping_type import CategoryShippingType
from .request_log import RequestLog
from .product_details_v2 import ProductDetailsV2
from .ram_event import RamEvent
from .tbl_index import TblIndex
from .sellable_product_barcodes import SellableProductBarcode
from .sellable_product_sub_sku import SellableProductSubSku
from .platform_sellers import PlatformSellers
from .product_categories import ProductCategory
from .sellable_product_price import SellableProductPrice

MANUFACTURE_CODE = 'manufacture'
