# coding=utf-8
import logging

from .base import fake
from .models import (
    BrandProvider,
    ColorProvider,
    UnitProvider,
    MiscProvider,
    CategoryProvider,
    MasterCategoryProvider,
    AttributeSetProvider,
    AttributeGroupProvider,
    AttributeProvider,
    ProductProvider,
    LogProductEditProvider,
    AttributeSetConfigDetailProvider,
    FileImportProvider,
    SellerProvider,
    ResultImportProvider,
    TerminalProvider,
    SellerTerminalProvider,
    SellableProductTerminalProvider,
    UserProvider,
    TaxProvider,
    ShippingPolicyProvider,
    TerminalGroupProvider,
    SellableProductTagProvider,
    FailedVariantImageRequestProvider, ShippingTypeProvider, SellableProductShippingTypeProvider,
    CategoryShippingTypeProvider,
    ProductCategoryProvider
)
from .msg import SRMRequestProvider

__author__ = 'Kien'
_logger = logging.getLogger(__name__)

fake.add_provider(BrandProvider)
fake.add_provider(ColorProvider)
fake.add_provider(UnitProvider)
fake.add_provider(CategoryProvider)
fake.add_provider(MasterCategoryProvider)
fake.add_provider(AttributeSetProvider)
fake.add_provider(MiscProvider)
fake.add_provider(AttributeGroupProvider)
fake.add_provider(AttributeProvider)
fake.add_provider(ProductProvider)
fake.add_provider(LogProductEditProvider)
fake.add_provider(AttributeSetConfigDetailProvider)
fake.add_provider(SellerProvider)
fake.add_provider(SRMRequestProvider)
fake.add_provider(FileImportProvider)
fake.add_provider(TerminalProvider)
fake.add_provider(SellerTerminalProvider)
fake.add_provider(SellableProductTerminalProvider)
fake.add_provider(UserProvider)
fake.add_provider(TaxProvider)
fake.add_provider(ShippingPolicyProvider)
fake.add_provider(TerminalGroupProvider)
fake.add_provider(SellableProductTagProvider)
fake.add_provider(FailedVariantImageRequestProvider)
fake.add_provider(ResultImportProvider)
fake.add_provider(ShippingTypeProvider)
fake.add_provider(SellableProductShippingTypeProvider)
fake.add_provider(CategoryShippingTypeProvider)
fake.add_provider(ProductCategoryProvider)
