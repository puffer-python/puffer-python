import copy

from catalog import models
from catalog.constants import SUB_SKU_POSTFIX
from catalog.services.categories.category import ProductCategoryService
from sqlalchemy.orm import load_only
from catalog.services.products import ProductService
from catalog.services.products.sellable import SellableProductListQuery, SubSkuListQuery
from catalog.services.seller import get_default_platform_owner_of_seller, get_platform_owner

product_service = ProductService.get_instance()


class SkuService:
    @staticmethod
    def create_list_sku(data):
        product_layer_data = SkuService.data_correction_for_product_layer(data)
        if data.get('product_id'):
            product = SkuService.update_product(product_layer_data, data)
        else:
            product = product_service.create_product(
                data=product_layer_data,
                email=product_layer_data['created_by']
            )
        return {
            'product_id': product.id,
            'provider_id': product.provider_id,
            'attribute_set_id': product.attribute_set_id
        }

    @staticmethod
    def data_correction_for_product_layer(data):
        """ Put data to the right layer """
        copy_data = copy.deepcopy(data)
        copy_data.pop('product_id', None)
        copy_data.pop('seller_id', None)
        copy_data.pop('variants', None)

        return copy_data

    @staticmethod
    def _set_sku_category(items, params):
        seller_ids = params.get('seller_ids')
        platform_id = params.get('platform_id')
        if not seller_ids:
            seller_ids = [item.seller_id for item in items]
        else:
            new_seller_ids = []
            for seller_id in seller_ids:
                try:
                    new_seller_ids.append(int(seller_id))
                except ValueError:
                    pass
            seller_ids = new_seller_ids
        seller_ids = list(set(seller_ids))

        platform_owner_seller_ids = []
        default_platform_owner_seller_ids = [get_default_platform_owner_of_seller(seller_id)
                                             for seller_id in seller_ids]
        if platform_id:
            platform_owner = get_platform_owner(platform_id)
            platform_owner_seller_ids = [platform_owner for _ in seller_ids]
        else:
            platform_owner_seller_ids.extend(default_platform_owner_seller_ids)

        product_ids = [item.product_id for item in items]

        items_platform_categories = ProductCategoryService.get_product_category(product_ids, platform_owner_seller_ids)
        items_default_platform_categories = ProductCategoryService.get_product_category(product_ids,
                                                                                        default_platform_owner_seller_ids)

        for item in items:
            item.platform_category = None
            seller_id_index = seller_ids.index(item.seller_id)

            platform_owner_seller_id = platform_owner_seller_ids[seller_id_index]

            for ipc in items_platform_categories:
                if ipc.category.seller_id == platform_owner_seller_id and ipc.product_id == item.product_id:
                    item.platform_category = ipc.category
                    break

            default_platform_owner_seller_id = default_platform_owner_seller_ids[seller_id_index]

            for default_category in items_default_platform_categories:
                if default_category.category.seller_id == default_platform_owner_seller_id and \
                        default_category.product_id == item.product_id:
                    item.default_category = default_category.category
                    break

    @staticmethod
    def _get_category_path(categories, model: models.db.Model):
        parent_ids = set()
        map_cats = {}
        for c in categories:
            path = list(map(lambda x: int(x), c.path.split('/')))
            map_cats[c.id] = (c, path)
            for id in path:
                parent_ids.add(id)
        parents = model.query.filter(model.id.in_(parent_ids)).all()
        parents = {i.id: i for i in parents}
        for (id, item) in map_cats.items():
            path = ''
            cat, cat_parent_ids = item
            for parent_id in cat_parent_ids:
                parent = parents.get(parent_id)
                if parent:
                    path = f'{path} / {parent.name}' if path else parent.name
            cat.ext_full_path_data = path
        return {i.id: i for i in categories}

    @staticmethod
    def _set_sku_extension_data(items):
        brand_ids = set()
        attribute_set_ids = set()
        editing_status_codes = set()
        sku_ids = set()
        product_ids = set()
        variant_ids = set()
        category_ids = set()
        master_category_ids = set()
        for item in items:
            brand_ids.add(item.brand_id)
            attribute_set_ids.add(item.attribute_set_id)
            editing_status_codes.add(item.editing_status_code)
            sku_ids.add(item.id)
            product_ids.add(item.product_id)
            variant_ids.add(item.variant_id)
            category_ids.add(item.category_id)
            if item.master_category_id:
                master_category_ids.add(item.master_category_id)
        brands = models.Brand.query.filter(models.Brand.id.in_(brand_ids)).all()
        brands = {i.id: i for i in brands}
        attribute_sets = models.AttributeSet.query.filter(models.AttributeSet.id.in_(attribute_set_ids)).all()
        attribute_sets = {i.id: i for i in attribute_sets}
        editing_statuses = models.EditingStatus.query.filter(models.EditingStatus.code.in_(editing_status_codes)).all()
        editing_statuses = {i.code: i for i in editing_statuses}
        products = models.Product.query.filter(models.Product.id.in_(product_ids)).options(
            load_only('id', 'name', 'model')).all()
        products = {i.id: i for i in products}
        variants = models.ProductVariant.query.filter(models.ProductVariant.id.in_(variant_ids)).options(
            load_only('id', 'url_key')).all()
        variants = {i.id: i for i in variants}
        variant_images = models.VariantImage.query.filter(models.VariantImage.product_variant_id.in_(variant_ids)).all()
        map_variant_images = {}
        for img in variant_images:
            values = map_variant_images.get(img.product_variant_id)
            if values:
                values.append(img)
            else:
                values = [img]
            map_variant_images[img.product_variant_id] = values
        master_categories = models.MasterCategory.query.filter(models.MasterCategory.id.in_(master_category_ids)).all()
        master_categories = SkuService._get_category_path(master_categories, models.MasterCategory)
        source_barcodes = models.SellableProductBarcode.query.filter(
            models.SellableProductBarcode.sellable_product_id.in_(sku_ids)).all()
        barcodes = {}
        for sb in source_barcodes:
            values = barcodes.get(sb.sellable_product_id)
            if values:
                values.append(sb)
            else:
                values = [sb]
            barcodes[sb.sellable_product_id] = values

        shipping_types = models.SellableProductShippingType.query.filter(
            models.SellableProductShippingType.sellable_product_id.in_(sku_ids)).all()
        shipping_types = {i.sellable_product_id: i for i in shipping_types}

        for item in items:
            item.loaded_barcodes = True
            item.ext_brand_data = brands.get(item.brand_id, None)
            item.ext_attribute_set_data = attribute_sets.get(item.attribute_set_id)
            item.ext_editing_status_data = editing_statuses.get(item.editing_status_code)
            item.ext_product_data = products.get(item.product_id, None)
            item.ext_product_variant_data = variants.get(item.variant_id, None)
            item.ext_variant_images_data = map_variant_images.get(item.variant_id)
            if item.master_category_id:
                item.ext_master_category_data = master_categories.get(item.master_category_id)
            item.ext_barcodes_data = barcodes.get(item.id)
            item.ext_shipping_type_data = shipping_types.get(item.id)

    @staticmethod
    def get_list_skus(params):
        page = params.get('page')
        page_size = params.get('page_size')
        if params.get('skus') and SUB_SKU_POSTFIX in ''.join(params.get('skus', [])):
            page = 1
            query = SubSkuListQuery()
            query.apply_filters(**params)
            query.pagination(page, len(params.get('skus')))
            items = []
            sub_skus = query.all()
            for sub_sku in sub_skus:
                parent = copy.copy(sub_sku.sellable_product)
                parent = SkuService._set_sub_sku(sub_sku, parent)
                items.append(parent)
            query = SellableProductListQuery()
            query.apply_filters(**params, restrict_seller=False)
            query.pagination(page, len(params.get('skus')))
            normal_items = query.all()
            items = items + normal_items
            total = len(items)
            page_size = max(10, total)
        else:
            query = SellableProductListQuery()
            query.apply_filters(**params, restrict_seller=False)
            total = len(query)
            query.pagination(page, page_size)
            items = query.all()

        if items:
            SkuService._set_sku_extension_data(items)
            SkuService._set_sku_category(items, params)

        return {
            'page': page,
            'page_size': page_size,
            'totalRecords': total,
            'products': items
        }

    @staticmethod
    def _set_sub_sku(sub_sku, parent_sku):
        parent_sku.is_sub = True
        parent_sku.sub_id = sub_sku.id
        parent_sku.sub_sku = sub_sku.sub_sku
        return parent_sku

    @staticmethod
    def update_product(product_layer_data, data):
        product = product_service.update_product(product_layer_data, data.get('product_id'))
        return product

    @staticmethod
    def add_provider_to_sku_params(data):
        skus = models.SellableProduct.query.filter_by(
            product_id=data.get('product_id')
        ).all()

        if not data.get('variants'):
            data['variants'] = []

        for sku in skus:
            existed_variant_payload = False
            for variant_payload in data['variants']:
                if sku.variant_id == variant_payload.get('variant_id'):
                    if not variant_payload.get('sku'):
                        variant_payload['sku']['sku'] = sku.sku
                    existed_variant_payload = True

            if not existed_variant_payload:
                data['variants'].append({
                    'variant_id': sku.variant_id,
                    'sku': {
                        'sku': sku.sku
                    }
                })
