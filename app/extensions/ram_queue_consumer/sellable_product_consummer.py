import logging
import json
from datetime import timedelta

from catalog import models as m
from catalog.utils import safe_cast
from sqlalchemy import or_
from sqlalchemy.orm import load_only
from catalog.extensions.ram_queue_consumer.sellable_product_advanced_info import AdvancedInfo

_author_ = 'Quang.LM'

_logger = logging.getLogger(__name__)

_MAP_STATUS = {
    'hang_ban': 1,
    'hang_sap_het': 2,
    'hang_moi': 3,
    'hang_trung_bay': 4,
    'hang_thanh_ly': 5,
    'hang_dat_truoc': 6,
    'ngung_kinh_doanh': 7
}


def _format_json_datetime(data):
    """
    Convert time to database time because when get datetime from database we subtracted 7h in BaseTimeStamp of model
    """
    base_time = data - timedelta(hours=7)
    return base_time.strftime('%Y-%m-%d %H:%M:%S.%f')


def _format_json(data, default_value=None):
    return json.dumps(data, ensure_ascii=False) if data else default_value


def _init_default(fields):
    response = {}
    for f in fields:
        response[f] = None
    return response


def _get_tax(tax):
    if tax == 'KT' or tax == '00':
        return 0
    return safe_cast(tax, int)


def _get_selling_status(sellable_product):
    status = sellable_product.selling_status_code
    if sellable_product.is_bundle and status == 'active':
        status = 'hang_ban'
    elif not status:
        status = 'hang_dat_truoc'
    return status, _MAP_STATUS.get(status, 8)


def _get_editing_status(sellable_product):
    return sellable_product.editing_status_code


def _get_publish_status(sellable_product):
    return 1 if sellable_product.editing_status_code in ('active', 'editing') else 0


def _get_need_manage_stock():
    # Now, always set to 1
    return 1


def _get_status(sellable_product):
    selling_status, priority = _get_selling_status(sellable_product)
    editing_status = _get_editing_status(sellable_product)
    publish_status = _get_publish_status(sellable_product)
    need_manage_stock = _get_need_manage_stock()
    return {
        'selling_status_code': selling_status,
        'editing_status': editing_status,
        'publish_status': publish_status,
        'need_manage_stock': need_manage_stock,
        'priority': priority,
    }


def _get_display_name(seo, advanced_info):
    if seo and seo.display_name:
        return seo.display_name
    seo_config = advanced_info.get('config_seo') or {}
    return seo_config.get('seo_name') or ''


def _get_smart_showroom(advanced_info):
    default_seo = advanced_info.get('default_seo') or {}
    return default_seo.get('smart_showroom') or ''


def _get_seo_by_field(seo, seo_config, field):
    if seo:
        value = getattr(seo, field)
        if value:
            return value
    return seo_config.get(field) or ''


def _get_master_categories(categories):
    response = []
    for c in categories:
        response.append({
            'id': c.id,
            'code': c.code,
            'name': c.name,
            'level': c.depth,
            'parent_id': c.parent_id,
        })
    return response


def _get_categories(categories):
    def _format(item):
        return {
            'id': item.id,
            'code': item.code,
            'name': item.name,
            'level': item.depth,
            'parent_id': item.parent_id,
            'is_adult': item.is_adult
        }

    response = []
    for cat in categories:
        response.append({
            'platform_id': cat.get('platform_id'),
            'owner_seller_id': cat.get('seller_id'),
            'categories': list(map(lambda c: _format(c), cat.get('platform_categories')))})
    return response


def _get_config_seo(seo, advanced_info):
    seo_config = advanced_info.get('config_seo') or {}
    return {
        'meta_keyword': _get_seo_by_field(seo, seo_config, 'meta_keyword'),
        'short_description': _get_seo_by_field(seo, seo_config, 'short_description'),
        'description': _get_seo_by_field(seo, seo_config, 'description'),
        'meta_title': _get_seo_by_field(seo, seo_config, 'meta_title'),
        'meta_description': _get_seo_by_field(seo, seo_config, 'meta_description'),
    }


class ProductDetail:

    def __init__(self, session):
        self.session = session

    def __get_seller(self, sellable_product):
        seller = self.session.query(m.Seller).filter(m.Seller.id == sellable_product.seller_id).first()
        if seller:
            return {
                'id': seller.id,
                'name': seller.name,
                'display_name': seller.display_name,
            }
        return _init_default(('id', 'name', 'display_name'))

    def __get_seo(self, sellable_product):
        seo = self.session.query(m.SellableProductSeoInfoTerminal).filter(
            m.SellableProductSeoInfoTerminal.sellable_product_id == sellable_product.id).first()
        return seo

    def __get_url_key(self, seo, sellable_product):
        if seo and seo.url_key:
            return seo.url_key
        variant = self.session.query(m.ProductVariant).filter(
            m.ProductVariant.id == sellable_product.variant_id).first()
        return variant.url_key if variant else ''

    def __get_product_type(self, sellable_product):
        misc = self.session.query(m.Misc).filter(m.Misc.type == 'product_type',
                                                 m.Misc.code == sellable_product.product_type).first()
        if misc:
            return {
                'code': misc.code,
                'name': misc.name,
            }
        return {
            'code': 'product',
            'name': 'Sản phẩm vật lý'
        }

    def __get_images(self, sellable_product):
        images = self.session.query(m.VariantImage).filter(
            m.VariantImage.product_variant_id == sellable_product.variant_id,
            m.VariantImage.status == 1, m.VariantImage.is_displayed == 1
        ).order_by(m.VariantImage.priority).all()
        response = []
        for img in images:
            response.append({
                'url': img.url,
                'path': img.path or '',
                'priority': img.priority,
                'label': img.label,
            })
        return response

    def __get_color(self, sellable_product):
        color = self.session.query(m.Color).filter(m.Color.id == sellable_product.color_id).first()
        if color:
            return {
                'code': color.code,
                'name': color.name,
            }
        return None

    def __get_barcodes(self, sellable_product):
        barcodes = self.session.query(m.SellableProductBarcode). \
            filter(m.SellableProductBarcode.sellable_product_id == sellable_product.id).all()
        return barcodes

    def __get_category_tree(self, sellable_product):
        sku_categories = self.session.query(m.ProductCategory).filter(
            m.ProductCategory.product_id == sellable_product.product_id).all()
        leaf_category_ids = list(map(lambda x: x.category_id, sku_categories))
        leaf_categories = self.session.query(m.Category).filter(m.Category.id.in_(leaf_category_ids)) \
            .order_by(m.Category.depth, m.Category.path).all()
        seller_ids = list(map(lambda x: x.seller_id, leaf_categories))
        platforms = self.session.query(m.PlatformSellers).filter(m.PlatformSellers.seller_id.in_(seller_ids),
                                                                 m.PlatformSellers.is_owner.is_(True)).all()
        ids = []
        root_ids = {}
        for cat in leaf_categories:
            platform_category_ids = list(map(lambda x: safe_cast(x, int), filter(lambda x: x, cat.path.split('/'))))
            root_ids[cat.seller_id] = platform_category_ids[0]
            ids.extend(platform_category_ids)
        all_categories = self.session.query(m.Category).filter(m.Category.id.in_(ids)) \
            .order_by(m.Category.depth, m.Category.path).all()
        categories = []
        for platform in platforms:
            platform_categories = list(filter(lambda x: x.seller_id == platform.seller_id, all_categories))
            categories.append({'platform_id': platform.platform_id, 'seller_id': platform.seller_id,
                               'platform_categories': platform_categories})

        return categories

    def __get_master_category_tree(self, sellable_product):
        if not sellable_product.master_category_id:
            return []
        cat = self.session.query(m.MasterCategory).filter(
            m.MasterCategory.id == sellable_product.master_category_id).first()
        ids = list(map(lambda x: safe_cast(x, int), filter(lambda x: x, cat.path.split('/'))))
        return self.session.query(m.MasterCategory).filter(m.MasterCategory.id.in_(ids)) \
            .order_by(m.MasterCategory.depth, m.MasterCategory.path).all()

    def __get_attribute_set(self, sellable_product):
        attribute_set = self.session.query(m.AttributeSet).filter(
            m.AttributeSet.id == sellable_product.attribute_set_id).first()
        if attribute_set:
            return {
                'id': attribute_set.id,
                'name': attribute_set.name,
            }
        return _init_default(('id', 'name'))

    def __get_brand(self, sellable_product):
        brand = self.session.query(m.Brand).filter(m.Brand.id == sellable_product.brand_id).first()
        if brand:
            return {
                'id': brand.id,
                'code': brand.code,
                'name': brand.name,
                'description': ''
            }
        return _init_default(('code', 'name'))

    def __get_shipping_types(self, sellable_product):
        shipping_types = self.session.query(
            m.ShippingType
        ).join(
            m.SellableProductShippingType,
            m.SellableProductShippingType.shipping_type_id == m.ShippingType.id
        ).filter(m.SellableProductShippingType.sellable_product_id == sellable_product.id).all()
        return list(map(lambda x: x.code, shipping_types))

    def __get_sellable_product_by_sku(self, sku):
        return self.session.query(m.SellableProduct).filter(m.SellableProduct.sku == sku).first()

    def __get_sellable_product_bundle(self, sellable_product_id):
        query = self.session.query(m.SellableProduct).filter(
            m.SellableProduct.id == sellable_product_id).options(load_only('sku', 'name'))
        return query.first()

    def __get_bundles(self, sellable_product):
        sku_id = sellable_product.id
        bundles = self.session.query(m.SellableProductBundle).filter(
            or_(m.SellableProductBundle.bundle_id == sku_id,
                m.SellableProductBundle.sellable_product_id == sku_id)).all()

        response = {}
        for b in bundles:
            if b.bundle_id == sku_id:
                child = self.__get_sellable_product_bundle(b.sellable_product_id)
                if child:
                    response['bundle_products'] = {
                        'sku': child.sku,
                        'quantity': b.quantity,
                        'priority': b.priority,
                        'name': child.name,
                        'seo_name': None
                    }
            elif b.sellable_product_id == sku_id:
                parent = self.__get_sellable_product_bundle(b.bundle_id)
                if parent:
                    response['parent_bundles'] = {
                        'sku': parent.sku,
                        'name': parent.name,
                    }
        return response

    def __get_tags(self, sellable_product):
        tag = self.session.query(m.SellableProductTag).filter(
            m.SellableProductTag.sellable_product_id == sellable_product.id).first()
        if not tag or not tag.tags:
            return []
        tags = tag.tags.split(',')
        return list(filter(lambda x: x, tags))

    def __get_advanced_info(self, sellable_product):
        advanced = AdvancedInfo(self.session)
        return advanced.get_advanced_info(sellable_product)

    def init_product_detail_v2(self, sku, updated_by):
        sellable_product = self.__get_sellable_product_by_sku(sku)
        if not sellable_product:
            return {}
        categories = self.__get_category_tree(sellable_product)
        master_categories = self.__get_master_category_tree(sellable_product)
        bundles = self.__get_bundles(sellable_product)
        images = self.__get_images(sellable_product)
        color = self.__get_color(sellable_product)
        seo = self.__get_seo(sellable_product)
        advanced_info = self.__get_advanced_info(sellable_product)
        barcodes = self.__get_barcodes(sellable_product)
        response = {
            'sku': sellable_product.sku,
            'seller_sku': sellable_product.seller_sku,
            'uom_code': sellable_product.uom_code,
            'uom_name': sellable_product.uom_name,
            'uom_ratio': sellable_product.uom_ratio,
            'seller_id': sellable_product.seller_id,
            'seller': _format_json(self.__get_seller(sellable_product)),
            'provider': _format_json({
                'id': sellable_product.provider_id
            }),
            'name': sellable_product.name,
            'url': self.__get_url_key(seo, sellable_product),
            'type': _format_json(self.__get_product_type(sellable_product)),
            'barcode': sellable_product.barcode,
            'barcodes': json.dumps([{'barcode': barcode.barcode,
                                     'source': barcode.source,
                                     'is_default': barcode.is_default} for barcode in barcodes]),
            'tax': _format_json({
                'tax_out_code': sellable_product.tax_out_code,
                'tax_in_code': sellable_product.tax_in_code,
                'tax_out': _get_tax(sellable_product.tax_out_code),
                'tax_in': _get_tax(sellable_product.tax_in_code),
            }),
            'images': _format_json(images),
            'display_name': _get_display_name(seo, advanced_info),
            'color': _format_json(color) if color else None,
            'product_line': '{}',
            'channels': None,
            'attribute_set': _format_json(self.__get_attribute_set(sellable_product)),
            'attributes': _format_json(advanced_info.get('attributes')),
            'categories': '[]',
            'platform_categories': _format_json(_get_categories(categories)),
            'seller_categories': _format_json(_get_master_categories(master_categories)),
            'brand': _format_json(self.__get_brand(sellable_product)),
            'status': _format_json(_get_status(sellable_product)),
            'smart_showroom': _get_smart_showroom(advanced_info),
            'seo_info': _format_json(_get_config_seo(seo, advanced_info)),
            'warranty': _format_json({
                'months': sellable_product.warranty_months,
                'description': sellable_product.warranty_note
            }),
            'sku_created_at': _format_json_datetime(sellable_product.created_at),
            'bundle_products': _format_json(bundles.get('bundle_products')) if bundles else None,
            'parent_bundles': _format_json(bundles.get('parent_bundles')) if bundles else None,
            'tags': _format_json(self.__get_tags(sellable_product), '[]'),
            'is_bundle': sellable_product.is_bundle,
            'attribute_groups': _format_json(advanced_info.get('attribute_groups')),
            'product_group': _format_json(advanced_info.get('product_group')),
            'serial_managed': sellable_product.tracking_type,
            'serial_generated': sellable_product.auto_generate_serial,
            'manufacture': _format_json(advanced_info.get('manufacture')),
            'shipping_types': _format_json(self.__get_shipping_types(sellable_product)),
            'updated_by': updated_by
        }
        return response
