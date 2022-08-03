# coding=utf-8
import logging

import blinker

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)

signals = blinker.Namespace()

product_created_signal = signals.signal('product-created')
on_product_created = product_created_signal.connect

product_common_data_updated_signal = signals.signal('product-data-updated')
on_product_common_data_updated = product_common_data_updated_signal.connect

product_status_updated_signal = signals.signal('product-status-updated')
on_product_status_updated = product_status_updated_signal.connect

upload_image_cloud_signal = signals.signal('upload-image-cloud')
on_upload_image_cloud = upload_image_cloud_signal.connect

create_variant_images_signal = signals.signal('create-variant-image')
on_create_variant_images = create_variant_images_signal.connect

product_import_signal = signals.signal('product-import')
on_product_import = product_import_signal.connect

product_basic_info_import_signal = signals.signal('product-basic-info-import')
on_product_basic_info_import = product_basic_info_import_signal.connect

update_product_import_signal = signals.signal('update-product-import')
on_update_product_import = update_product_import_signal.connect

update_attribute_product_import_signal = signals.signal('update-attribute-product-import')
on_update_attribute_product_import = update_attribute_product_import_signal.connect

create_product_quickly = signals.signal('import-create-product-quickly')
on_create_product_quickly = create_product_quickly.connect

product_create_import_signal = signals.signal('product-import-created')
on_product_created_import = product_create_import_signal.connect

sellable_create_signal = signals.signal('sellable-created')
on_sellable_create = sellable_create_signal.connect

sellable_update_signal = signals.signal('sellable-updated')
on_sellable_update = sellable_update_signal.connect

sellable_common_update_signal = signals.signal('sellable-common-updated')
on_sellable_common_update = sellable_common_update_signal.connect

sellable_update_seo_info_signal = signals.signal('sellable-seoinfo-updated')
on_sellable_update_seo_info = sellable_update_seo_info_signal.connect

product_update_seo_info_import_signal = signals.signal('product-import-seo-info-updated')
on_update_seo_info_import = product_update_seo_info_import_signal.connect

product_update_editing_status_import_signal = signals.signal('product-import-editing-status-updated')
on_product_editing_status_updated_import = product_update_editing_status_import_signal.connect

update_product_tag_import_signal = signals.signal('update-product-tag-imported')
on_update_product_tag_imported = update_product_tag_import_signal.connect

update_product_terminal_groups_import_signal = signals.signal('update-product-terminal-groups-imported')
on_update_product_terminal_groups_imported = update_product_terminal_groups_import_signal.connect

upsert_product_category_import_signal = signals.signal('upsert-product-category-imported')
on_upsert_product_category_imported = upsert_product_category_import_signal.connect

brand_created_signal = signals.signal('brand_created')
on_brand_created = brand_created_signal.connect

brand_updated_signal = signals.signal('brand_updated')
on_brand_updated = brand_updated_signal.connect

brand_deleted_signal = signals.signal('brand_deleted')
on_brand_deleted = brand_deleted_signal.connect

unit_created_signal = signals.signal('unit_created')
on_unit_created = unit_created_signal.connect

unit_updated_signal = signals.signal('unit_updated')
on_unit_updated = unit_updated_signal.connect

category_created_signal = signals.signal('category_created')
on_category_created = category_created_signal.connect

category_updated_signal = signals.signal('category_updated')
on_category_updated = category_updated_signal.connect

unit_deleted_signal = signals.signal('unit_deleted')
on_unit_deleted = unit_deleted_signal.connect

listing_update_signal = signals.signal('listing_update')
on_listing_update = listing_update_signal.connect

attribute_set_created_signal = signals.signal('attribute_set_created')
on_attribute_set_created = attribute_set_created_signal.connect

attribute_updated_signal = signals.signal('attribute_updated')
on_attribute_updated = attribute_updated_signal.connect

attribute_option_updated_signal = signals.signal('attribute_option_updated')
on_attribute_option_updated = attribute_option_updated_signal.connect

clone_master_category_request_signal = signals.signal('clone_master_category_request')
on_clone_master_category_request = clone_master_category_request_signal.connect

category_apply_shipping_type_to_sku_signal = signals.signal('category_apply_shipping_type_to_sku')
on_category_apply_shipping_type_to_sku = category_apply_shipping_type_to_sku_signal.connect

update_images_skus_import_signal = signals.signal('update_images_skus_import')
on_update_images_skus_import = update_images_skus_import_signal.connect

ram_category_created_signal = signals.signal('ram_category_created')
on_ram_category_created = ram_category_created_signal.connect

ram_category_updated_signal = signals.signal('ram_category_updated')
on_ram_category_updated = ram_category_updated_signal.connect

sub_sku_created_signal = signals.signal('sub_sku_created')
on_sub_sku_created = sub_sku_created_signal.connect

platform_seller_upsert_created_signal = signals.signal('platform_seller_upsert_created')
on_platform_seller_upsert_created = platform_seller_upsert_created_signal.connect

export_product_signal = signals.signal('export_product')
on_export_product = export_product_signal.connect
