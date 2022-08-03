# coding=utf-8
import logging
import traceback

from flask import g
from flask_login import (
    login_required,
    current_user,
)

from catalog import log_request
from catalog.constants import ExportSellable
from catalog.extensions import flask_restplus as fr
from catalog.extensions import signals
from catalog.services.products import sellable as service
from catalog.services.products import ProductVariantService
from catalog.validators import sellable as validator
from catalog.validators.sellable import (
    GetItemsBundleValidator,
)
from catalog.extensions import exceptions as exc
from . import schema

import catalog.services.categories.category as category_service

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)

sellable_ns = fr.Namespace(
    name='sellable_product',
    path='/sellable_products'
)

variant_service = ProductVariantService.get_instance()


def _update_barcode(data):
    if data.get('barcode'):
        barcode = data.pop('barcode')
        data['barcodes'] = [{'barcode': barcode, 'source': None}]


@sellable_ns.route('', methods=['GET', 'POST'])
class SellableProducts(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.SellableProductsRequest, location='body')
    @sellable_ns.marshal_with(schema_cls=schema.SellableProductSchema, many=True)
    @login_required
    def post(self):
        data = g.body
        data['seller_id'] = current_user.seller_id
        validator.CreateSellableProductsValidator.validate(data)
        for item in data.get('sellable_products'):
            _update_barcode(item)
        return service.create_sellable_products(data)

    @log_request
    @sellable_ns.expect(schema_cls=schema.SellableProductListRequest, location='args')
    @sellable_ns.marshal_with(schema_cls=schema.SellableProductList)
    @login_required
    def get(self):
        export = g.args.pop('export')
        params = g.args
        params['seller_ids'] = [current_user.seller_id]
        if params.get('category') and export and export > 0:
            params['category_ids'] = params.pop('category')
        if export == ExportSellable.EXPORT_GENERAL_INFO:
            service.get_sellables_for_export(
                params=params, export_type=ExportSellable.EXPORT_GENERAL_INFO)
            return {}
        elif export == ExportSellable.EXPORT_ALL_ATTRIBUTE:
            service.get_sellables_for_export(
                params=params, include_attribute=True, export_type=ExportSellable.EXPORT_ALL_ATTRIBUTE)
            return {}
        elif export == ExportSellable.EXPORT_SEO_INFO:
            service.get_sellables_for_export(
                params=params, export_type=ExportSellable.EXPORT_SEO_INFO)
            return {}
        return service.get_sellable_products(params)


@sellable_ns.route('/<int:product_id>/<string:data_type>', methods=['GET'])
class SellableProduct(fr.Resource):
    @log_request
    @sellable_ns.marshal_with(schema_cls=schema.SellableProductDetail)
    @login_required
    def get(self, product_id, data_type):
        return service.get_sellable_product_detail(product_id, data_type)


@sellable_ns.route('/sku/<string:sku>/<string:data_type>', methods=['GET'])
class SellableProductWithSku(fr.Resource):
    @sellable_ns.marshal_with(schema_cls=schema.SellableProductDetail)
    @login_required
    def get(self, sku, data_type):
        return service.get_sellable_product_detail_by_sku(sku, data_type)


@sellable_ns.route('/<int:sellable_id>', methods=['PATCH'])
class UpdateSellableProduct(fr.Resource):
    @sellable_ns.expect(schema.UpdateCommonRequest, location='body')
    @sellable_ns.marshal_with(schema.UpdateCommonResponse)
    @login_required
    def patch(self, sellable_id):
        data = g.body
        validator.UpdateCommonValidator(sellable_id, is_sku=False).validate({
            'data': data
        })
        _update_barcode(data)
        updated_fields = service.update_common(sku_id=sellable_id, data=data)
        return updated_fields


@sellable_ns.route('/terminals', methods=['POST'])
@sellable_ns.route('/terminals/<string:terminal_code>/products', methods=['GET'])
class SellableProductTerminal(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.SellableProductTerminalSchema, location='body')
    @sellable_ns.marshal_with(schema_cls=schema.SellableProductTerminalSchema)
    @login_required
    def post(self):
        data = g.body
        validator.UpdateSellableProductTerminalValidator.validate(data)
        return service.set_sellable_terminal(
            data.get('skus'),
            data.get('seller_terminals')
        )

    @sellable_ns.expect(schema_cls=schema.SellableTerminalProductListRequest, location='args')
    @sellable_ns.marshal_with(schema_cls=schema.SellableProductList)
    @login_required
    def get(self, terminal_code):
        data = g.args
        data.update({'terminal': terminal_code})
        return service.get_sellable_products(
            restrict_seller=False,
            params=data
        )


@sellable_ns.route('/uom_info', methods=['GET'])
class SellableProductUomInfo(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.GetSkusBySellerSku, location='args')
    @sellable_ns.marshal_with(schema.GetSkusBySellerSkuResponse)
    @login_required
    def get(self):
        if g.args.get('seller_skus') or g.args.get('skus'):
            return service.get_skus_uom_info(g.args)
        else:
            raise exc.BadRequestException(
                'At least sellerSkus or skus field must be provided'
            )


@sellable_ns.route('/status', methods=['PATCH'])
class SellableProductStatus(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.UpdateEditingStatusRequestBody, location='body')
    @sellable_ns.marshal_with(schema.UpdateEditingStatusResponse)
    @login_required
    def patch(self):
        validator.UpdateEditingStatusValidator.validate({
            'seller_id': current_user.seller_id,
            **g.body
        })
        skus = service.update_sellable_editing_status(**g.body)
        return {
                   'ids': [sku.id for sku in skus],
                   'skus': [sku.sku for sku in skus]
               }, 'Cập nhật trạng thái thành công'


@sellable_ns.route('/apply', methods=['POST'])
class ApplySellableProducts(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.ApplySellableProductsRequest, location='body')
    @sellable_ns.marshal_with(schema_cls=schema.Schema)
    @login_required
    def post(self):
        body = g.body
        filter_cond = body.get('filter_condition') or {}
        category_id = filter_cond.get('category_id')
        if category_id:
            data = body.get('data') or {}
            shipping_type = data.get('shipping_type')
            if shipping_type:
                shipping_type_ids = shipping_type.get('ids', [])
                if not shipping_type_ids:
                    raise exc.BadRequestException(f'Danh sách loại hình vận chuyển không được để trống')
                category_service.apply_shipping_type_to_skus(category_id, shipping_type_ids)
        return {}, 'Áp dụng thành công'


@sellable_ns.route('/<int:sellable_id>/items', methods=['PUT', 'GET'])
class BundleSellableItem(fr.Resource):
    @sellable_ns.expect(schema.UpdateSellableBundleRequestBody, location='body')
    @sellable_ns.marshal_with(schema.UpdateSellableBundleResponse)
    @login_required
    def put(self, sellable_id):
        validator.UpdateItemBundleValidator.validate({
            'sellable_id': sellable_id,
            'seller_id': current_user.seller_id,
            **g.body
        })
        service.update_item_for_bundle_sellable(sellable_id, g.body['items'])
        return g.body


@sellable_ns.route('/<int:sellable_id>/bundle/skus', methods=['GET'])
class BundleSkus(fr.Resource):
    @sellable_ns.marshal_with(schema.GetSellableBundleResponseBody)
    @login_required
    def get(self, sellable_id):
        GetItemsBundleValidator.validate({
            'sellable_id': sellable_id
        })
        return {
            'items': service.get_sellable_products_in_bundle(sellable_id)
        }


@sellable_ns.route('/json_upsert', methods=['POST'])
class SellableJsonUpsert(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.SellableJsonUpsertSchema, location='body')
    @login_required
    def post(self):
        try:
            sellable_skus = g.body.get('skus')
            signals.listing_update_signal.send(sellable_skus)
            return 'Update successfully', 200
        except Exception as e:
            return {
                'type': e.__class__.__name__,
                'message': str(e),
                'traceback': '%s %s' % (
                    ''.join(traceback.format_tb(e.__traceback__)),
                    str(e)
                )
            }


@sellable_ns.route('/sku/<string:sku>/terminals/seo_info', methods=['GET'])
class SellableProductTerminalSEOInfoBySku(fr.Resource):
    @sellable_ns.expect(schema.GetSEOInfoRequest, location='args')
    @sellable_ns.marshal_with(schema.GetSEOInfoResponse)
    @login_required
    def get(self, sku):
        params = g.args

        validator.SEOInfoValidatorBySku.validate(params, **{
            "sku": sku,
            "seller_id": current_user.seller_id,
        })

        return service.get_seo_info_of_sellable_product_on_terminal(
            sku=sku, **params
        )


@sellable_ns.route('/<int:sellable_id>/terminals/seo_info', methods=['GET'])
class SellableProductTerminalSEOInfo(fr.Resource):
    @sellable_ns.expect(schema.GetSEOInfoRequest, location='args')
    @sellable_ns.marshal_with(schema.GetSEOInfoResponse)
    @login_required
    def get(self, sellable_id):
        params = g.args

        validator.SEOInfoValidatorById.validate(params, **{
            "sellable_id": sellable_id,
            "seller_id": current_user.seller_id,
        })

        return service.get_seo_info_of_sellable_product_on_terminal(
            sellable_id=sellable_id, **params
        )


@sellable_ns.route('/sku/<string:sku>/terminals/seo_info', methods=['PUT'])
class SellableProductTerminalsSEOInfoBySku(fr.Resource):
    @sellable_ns.expect(schema.PutSEOInfo, location='body', allow_none=False)
    @sellable_ns.marshal_with(schema.Schema)
    @login_required
    def put(self, sku):
        payload = g.body

        validator.SEOInfoValidatorBySku.validate(payload, **{
            "seller_id": current_user.seller_id,
            "sku": sku
        })

        service.upsert_info_of_sellable_product_on_terminals(
            sku=sku,
            **payload
        )
        return {}, "Thêm thông tin SEO thành công"


@sellable_ns.route('/<int:sellable_id>/terminals/seo_info', methods=['PUT'])
class SellableProductTerminalsSEOInfo(fr.Resource):
    @sellable_ns.expect(schema.PutSEOInfo, location='body', allow_none=False)
    @sellable_ns.marshal_with(schema.Schema)
    @login_required
    def put(self, sellable_id):
        payload = g.body

        validator.SEOInfoValidatorById.validate(payload, **{
            "seller_id": current_user.seller_id,
            "sellable_id": sellable_id
        })

        service.upsert_info_of_sellable_product_on_terminals(
            sellable_id=sellable_id,
            **payload
        )
        return {}, "Thêm thông tin SEO thành công"


@sellable_ns.route('/terminal_groups', methods=['POST'])
class SellableProductTerminalGroup(fr.Resource):
    @sellable_ns.expect(schema.SellableProductTerminalGroup, location='body', allow_none=True)
    @sellable_ns.marshal_with(schema.SellableProductTerminalGroup)
    @login_required
    def post(self):
        payload = g.body
        validator.UpsertSellableProductTerminalGroup.validate(payload)
        service.upsert_sellable_product_terminal_group(**payload)

        return payload


@sellable_ns.route('/terminal_groups/<string:terminal_group_code>/products', methods=['GET'])
class SellableProductsTerminalGroup(fr.Resource):
    @sellable_ns.expect(schema_cls=schema.SellableTerminalGroupProductListRequest, location='args')
    @sellable_ns.marshal_with(schema.SellableProductList)
    def get(self, terminal_group_code):
        params = g.args
        params.update({'terminal_group': terminal_group_code})
        return service.get_sellable_products(
            params=params, restrict_seller=False
        )


@sellable_ns.route('/import_update_categories', methods=['POST'])
class ImportCategories(fr.Resource):
    @sellable_ns.marshal_with(schema.Schema)
    @login_required
    def post(self):
        import time
        import pandas as pd
        from flask import request
        from catalog.services.categories import CategoryService
        cat_service = CategoryService.get_instance()
        files = request.files
        r = files.get('file')
        df = pd.io.excel.read_excel(r.stream, header=5, dtype=str)
        categories = {}
        seller_id = current_user.seller_id
        for _, (r) in df.iterrows():
            category_code = r[1]
            cat = categories.get(category_code)
            if not cat:
                cat = cat_service.get_category_with_code(category_code, seller_id)
                categories[category_code] = cat

            if cat:
                service.update_common(sku=r[0], data={'category_id': cat.id})
                time.sleep(0.1)
        return {}, 'Done'
