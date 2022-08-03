from flask import g
from flask_login import login_required, current_user

from catalog.extensions import flask_restplus as fr, signals
from catalog.services.products import ProductVariantService, ProductService
from catalog.services.products import sellable as sku_service
from catalog.services import seller as seller_service
from catalog.services.products import SkuService
from .create_list_sku_schema import CreateListSkuRequest, CreateListSkuResponse
from .create_list_sku_validator import validate_format, validate_move_sku_to_single_product, validate_variants_business, \
    validate_variant_attributes_business, validate_variant_images_business, validate_skus_business, \
    validate_update_sku_business
from catalog.extensions.request_logging import log_request
from .schema import GetListSkuRequest, GetListSkuResponse, Schema, CreateSubSKuResponse
from .sku_schema import MoveSkusRequest, UpdateSkuRequest, MoveSkuRequest
from ..product.schema import ProductHistory


sku_ns = fr.Namespace(
    name='list_sku',
    path='/create_list_sku'
)

_variant_service = ProductVariantService.get_instance()


def _upsert_product(product):
    if product.get('product_id') and (product.get('provider_id') or product.get('model')):
        SkuService.add_provider_to_sku_params(product)
    return SkuService.create_list_sku(product)


def _format_sku(product_id, variant_id, sku_data, common_data, variant_data):
    def __copy_data(field, data, target_field, target_data):
        if field in data:
            target_data[target_field] = data.get(field)

    def __copy_barcode(data, target_data):
        if 'barcode' in data:
            target_data['barcodes'] = sku_data.get('barcode') or []
            target_data['overwrite_barcodes'] = True
        if 'barcodes' in data:
            target_data['barcodes'] = sku_data.get('barcodes') or []

    def __copy_provider_id(target_data, seller_id):
        if 'provider_id' in common_data:
            target_data['provider_id'] = common_data.get('provider_id') or seller_id

    def __copy_shipping_type_id(field, data, target_field, target_data):
        if field in data:
            target_data[target_field] = [data.get(field)]

    def __copy_uom(data, target_data):
        if not data.get('variant_id'):
            target_data['uom_id'] = data.get('uom_id')
            target_data['uom_ratio'] = data.get('uom_ratio', 1)

    if not sku_data:
        return None

    seller_id = common_data.get('seller_id')
    created_by = common_data.get('created_by')
    response = {}

    # Product Layer
    __copy_data('category_id', common_data, 'category_id', response)
    __copy_data('master_category_id', common_data, 'master_category_id', response)
    __copy_data('warranty_months', common_data, 'warranty_months', response)
    __copy_data('warranty_note', common_data, 'warranty_note', response)
    __copy_data('brand_id', common_data, 'brand_id', response)
    __copy_data('model', common_data, 'model', response)
    __copy_data('tax_in_code', common_data, 'tax_in_code', response)
    __copy_provider_id(response, seller_id)

    # Variant Layer
    __copy_uom(variant_data, response)

    # Sku Layer
    __copy_data('name', sku_data, 'name', response)
    __copy_data('tracking_type', sku_data, 'tracking_type', response)
    __copy_data('expiry_tracking', sku_data, 'expiry_tracking', response)
    __copy_data('expiration_type', sku_data, 'expiration_type', response)
    __copy_data('days_before_exp_lock', sku_data, 'days_before_exp_lock', response)
    __copy_data('brand_id', sku_data, 'brand_id', response)
    __copy_data('category_id', sku_data, 'category_id', response)
    __copy_data('master_category_id', sku_data, 'master_category_id', response)
    __copy_data('attribute_set_id', sku_data, 'attribute_set_id', response)
    __copy_data('model', sku_data, 'model', response)
    __copy_data('tax_in_code', sku_data, 'tax_in_code', response)
    __copy_data('product_type', sku_data, 'product_type', response)
    __copy_data('part_number', sku_data, 'part_number', response)
    __copy_data('seller_sku', sku_data, 'seller_sku', response)
    __copy_data('description', sku_data, 'description', response)
    __copy_data('detailed_description', sku_data, 'detailed_description', response)
    __copy_data('editing_status_code', sku_data, 'editing_status_code', response)
    __copy_shipping_type_id('shipping_type_id', sku_data, 'shipping_types', response)
    __copy_barcode(sku_data, response)
    if response:
        __copy_data('sku', sku_data, 'sku', response)
        response['created_by'] = created_by
        response['variant_id'] = variant_id
        response['product_id'] = product_id
        response['manage_serial'] = False
        response['auto_generate_serial'] = False
    return response


def _create_variants_in_chain(product_id, tuple_variants, created_by):
    variant_ids = []
    for variant_attributes, _, variant_id in tuple_variants:
        if not variant_id and variant_attributes:
            variant_data = [{
                'attributes': variant_attributes
            }]
            upsert_variants = _variant_service.create_variants(
                product_id, variant_data, created_by, __not_bulk_commit=True)
            variant_id = upsert_variants[0].get('id')
        variant_ids.append(variant_id)
    return variant_ids


def _upsert_variant_attributes(tuple_variants, variant_ids, common_data):
    idx = 0
    variants = []
    for _, not_variant_attributes, _ in tuple_variants:
        if not_variant_attributes:
            variants.append({'id': variant_ids[idx], 'attributes': not_variant_attributes})
        idx += 1
    if variants:
        variant_data = {'variants': variants}
        validate_variant_attributes_business(variant_data, common_data.get('seller_id'))
        _variant_service.create_bulk_variant_attributes(variant_data, auto_commit=False)


def _upsert_variant_images(variant_ids, variants, created_by):
    idx = 0
    variant_images = []
    for variant_id in variant_ids:
        sku = variants[idx].get('sku')
        if sku and sku.get('images') is not None:
            variant_images.append({
                'id': variant_id,
                'images': sku.get('images')
            })
        idx += 1
    if variant_images:
        variant_image_data = {'variants': variant_images}
        validate_variant_images_business(variant_image_data)
        _variant_service.update_variant(variant_image_data, created_by=created_by)


def _upsert_sku(product_id, variant_ids, variants, common_data):
    def __get_data(product_id):
        idx = 0
        add_skus = []
        update_skus = []
        for variant_id in variant_ids:
            variant = variants[idx]
            sku = variants[idx].get('sku')
            sku_item = _format_sku(product_id, variant_id, sku, common_data, variant)
            if not sku_item:
                continue
            if sku.get('sku'):
                update_skus.append(sku_item)
            else:
                add_skus.append(sku_item)
            idx += 1
        return add_skus, update_skus

    def __insert_sku(add_skus):
        if add_skus:
            seller = seller_service.get_seller_by_id(common_data.get('seller_id'))
            return sku_service.create_sellable_products({'product_id': product_id, 'sellable_products': add_skus},
                                                        __not_bulk_commit=True,
                                                        seller=seller, sellable_create_signal=False)
        return [], ''

    def __update_skus(update_skus):
        return [
            sku_service.update_common(
                sku=sku.get('sku'),
                data=sku,
                autocommit=False,
                overwrite_barcode=sku.pop('overwrite_barcodes', False),
                sellable_common_update_signal=False,
                sellable_update_signal=False
            )
            for sku in update_skus
        ]

    def __get_response(variant_ids, skus):
        response = []
        for variant_id in variant_ids:
            item = {'variant_id': variant_id}
            for new_sku in skus:
                if new_sku.variant_id == variant_id:
                    item['sku_id'] = new_sku.id
                    item['sku'] = new_sku.sku
                    item['seller_sku'] = new_sku.seller_sku
            response.append(item)
        return response

    def __send_signals(insert_skus_result, update_skus_result):
        last_sku = None
        existing_sibling_sku_obj = update_skus_result[0] if update_skus_result else None
        for sku in insert_skus_result:
            last_sku = sku
            signals.sellable_create_signal.send(
                sku,
                allow_update_product_detail=False,
                existing_sibling_sku_obj=existing_sibling_sku_obj,
            )
        for sku in update_skus_result:
            last_sku = sku
            signals.sellable_common_update_signal.send(sku)
        if last_sku:
            signals.sellable_update_signal.send(last_sku)

    add_skus, update_skus = __get_data(product_id)
    validate_skus_business(product_id, add_skus, update_skus, common_data.get('seller_id'))
    skus = []

    insert_skus_result, _m = __insert_sku(add_skus)
    skus.extend(insert_skus_result)

    update_skus_result = __update_skus(update_skus)
    skus.extend(update_skus_result)

    # Must save before sending signal to sync data
    sku_service.save_changes()
    __send_signals(insert_skus_result, update_skus_result)
    return __get_response(variant_ids, skus)


def _upsert_list_variant_sku(product_id, attribute_set_id, variants, common_data):
    # Variants
    tuple_variants = validate_variants_business(product_id, attribute_set_id, variants, common_data)
    variant_ids = _create_variants_in_chain(product_id, tuple_variants, common_data.get('created_by'))

    # Attributes of variant
    _upsert_variant_attributes(tuple_variants, variant_ids, common_data)

    # Images of variant
    _upsert_variant_images(variant_ids, variants, common_data.get('created_by'))

    # Sku
    response = _upsert_sku(product_id, variant_ids, variants, common_data)

    return response


@sku_ns.route('', methods=['POST'])
class Products(fr.Resource):
    @log_request
    @sku_ns.expect(CreateListSkuRequest, location='body')
    @sku_ns.marshal_with(CreateListSkuResponse)
    def post(self):
        data = g.body
        validate_format(data)
        product = _upsert_product(data)
        variants = None
        if data.get('variants'):
            common_data = {
                **data
            }
            variants = _upsert_list_variant_sku(product.get('product_id'),
                                                product.get('attribute_set_id'),
                                                data.get('variants'), common_data)
        return {
            'product_id': product.get('product_id'),
            'variants': variants
        }


detail_sku_ns = fr.Namespace(
    name='get_list_sku',
    path='/skus'
)


@detail_sku_ns.route('', methods=['GET', 'PUT'])
class GetSkus(fr.Resource):
    @log_request
    @detail_sku_ns.expect(GetListSkuRequest, location='args')
    @detail_sku_ns.marshal_with(GetListSkuResponse)
    def get(self):
        params = g.args
        return SkuService.get_list_skus(params)

    @detail_sku_ns.expect(MoveSkusRequest, location='body')
    @detail_sku_ns.marshal_with(GetListSkuResponse)
    def put(self):
        data = g.body
        seller_id = data['seller_id']
        product_id = data['target_product_id']
        skus = data['skus']
        validate_move_sku_to_single_product(skus=skus, seller_id=seller_id, product_id=product_id)
        sku_service.move_skus_to_single_product(
            skus=skus,
            product_id=product_id
        )
        return {}, 'Cập nhật dữ liệu thành công'


@detail_sku_ns.route('/<string:sku>', methods=['PATCH'])
class SkuDetail(fr.Resource):
    __FC_SERVICE = 'FC'

    @log_request
    @sku_ns.expect(UpdateSkuRequest, location='body')
    @detail_sku_ns.marshal_with(Schema)
    def patch(self, sku):
        data = g.body
        seller_id = data.pop('seller_id', None)
        validate_update_sku_business(sku, data, seller_id=seller_id)
        created_by = data.get('created_by') or self.__FC_SERVICE
        data['created_by'] = created_by
        sku_service.update_common(
            sku=sku,
            data=data,
            overwrite_barcode=False
        )
        return {}, 'Cập nhật dữ liệu thành công'


@detail_sku_ns.route('/<string:sku>/history', methods=['GET'])
class ProductHistoryBySku(fr.Resource):
    @detail_sku_ns.marshal_with(ProductHistory, as_list=True)
    @login_required
    def get(self, sku):
        service = ProductService.get_instance()
        return service.get_product_history(sku=sku)


@detail_sku_ns.route('/<string:sku>/child', methods=['POST'])
class ProductSKuChild(fr.Resource):
    @detail_sku_ns.marshal_with(CreateSubSKuResponse)
    def post(self, sku):
        service = ProductService.get_instance()
        return service.create_sub_sku(sku=sku, created_by=current_user.email)


@detail_sku_ns.route('/<string:sku>/move-group', methods=['POST'])
class ProductMoveGroup(fr.Resource):
    @sku_ns.expect(MoveSkuRequest, location='body')
    def post(self, sku):
        service = ProductService.get_instance()
        return service.move_group(sku, g.body.get('sku'))
