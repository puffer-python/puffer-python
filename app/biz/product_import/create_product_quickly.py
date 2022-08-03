# pylint: disable=abstract-class-instantiated
import json
import logging

from catalog import models, celery, app
from sqlalchemy import func
from flask_login import current_user
from catalog.utils import keep_single_spaces
from catalog.extensions import signals, convert_int_field
from catalog.services.terminal import get_terminal_groups
from catalog.biz.result_import import CreateProductImportCapture, ImportStatus
from catalog.validators.sellable import CreateSellableProductsFromImportValidator
from catalog.biz.product_import.base import save_excel, Importer, read_excel
from catalog.services.products.sellable import create_sellable_products
from catalog.api.product.sellable.schema import SellableProductsRequest
from catalog.services.shipping_types.shipping_type import get_shipping_type_by_category_id

_logger = logging.getLogger(__name__)
__author__ = 'Dung.BV'


class CreateProductQuicklyTask:

    def __init__(self, file_id, cls_importer):
        self.cls_importer = cls_importer
        self.process = models.FileImport.query.get(file_id)  # type: models.FileImport
        self.user = models.IAMUser.query.filter(
            models.IAMUser.email == self.process.created_by
        ).first()
        self.reader_index = []
        self.idx = 0
        self.result = {}
        self.skus = {}
        self.total_row_success = 0
        self.total_row = 0

        self.reader = read_excel(self.process.path, header=5)
        self.skip_blank_lines()

    def run(self):
        try:
            self._init_ratio()
            self.import_process()
            self._remove_ratio_column()
            self.save_result()
        except:
            self.process.status = 'error'

    def init_current_user(self):
        self.user.seller_id = self.process.seller_id

    def save_result(self):
        num_of_columns = len(self.reader.columns)
        if len(self.skus) > 0:
            self.reader.insert(num_of_columns, 'SKU', self.convert_skus_to_list())
            num_of_columns += 1
        self.reader.insert(num_of_columns, 'Kết quả', self.convert_result_to_list())
        self.process.total_row_success = self.total_row_success
        self.process.total_row = self.total_row
        self.process.success_path = save_excel(self.reader)
        self.process.status = 'done'
        models.db.session.commit()

    def import_process(self):
        self.process.status = 'processing'
        models.db.session.commit()
        self.import_data()

    def import_data(self):
        while self.idx < len(self.reader_index):
            i = self.reader_index[self.idx]
            self.total_row += 1
            try:
                self.import_data_row()
            except Exception as e:
                _logger.exception(e)
                self.result[i] = 'File chứa ký tự không hợp lệ hoặc hệ thống gặp lỗi'
            self.idx += 1

    def import_data_row(self):
        i = self.reader_index[self.idx]
        importer = self.cls_importer(
            data=self.reader.loc[i],
            process=self.process,
            import_type='don',
        )
        with CreateProductImportCapture(
                attribute_set_id=importer.attribute_set_id, parent_row=None,
                import_id=self.process.id, importer=importer) as capture:
            result_import = importer.import_row_don()
            if result_import is None:
                self.result[i] = 'Thành công'
                self.total_row_success = self.total_row_success + 1
                capture.status = ImportStatus.SUCCESS
                capture.product_id = importer.product.id
                if not importer.row.get('sku'):
                    if importer.sku:
                        importer.row['sku'] = importer.sku.sku
                        self.skus[i] = importer.sku.sku
                    else:
                        self.skus[i] = ''
            else:
                self.result[i] = result_import
                capture.status = ImportStatus.FAILURE
            capture.data = importer.row.to_dict()
            capture.message = str(self.result[i])

    def skip_blank_lines(self):
        for i in self.reader.index:
            self.reader_index.append(i)

    def convert_result_to_list(self):
        tmp_result = []
        for i in sorted(list(self.result.keys())):
            tmp_result.append(self.result[i])
        return tmp_result

    def convert_skus_to_list(self):
        if len(self.skus) == 0:
            return []
        tmp_skus = []
        for i in sorted(list(self.result.keys())):
            tmp_skus.append(self.skus.get(i))
        return tmp_skus

    def _init_ratio(self):
        ratios = []
        for _ in self.reader.index:
            ratios.append('1.0')
        self.reader.insert(0, 'uom_ratio', ratios)

    def _remove_ratio_column(self):
        self.reader.drop(labels='uom_ratio', axis=1)


class ImportProductQuickly(Importer):
    def init_attributes(self):
        default_attribute_set = models.AttributeSet.query.filter(models.AttributeSet.is_default == 1).first()
        if not default_attribute_set:
            raise RuntimeError("The worker required an default attribute set")
        self.attribute_set_id = default_attribute_set.id
        self.attribute_set = default_attribute_set
        self.attributes = self.attribute_set.get_variation_attributes()
        self.teminal_groups = get_terminal_groups(self.seller.id)
        self.specifications_attributes = self.attribute_set.get_specifications_attributes()

    def _get_terminal_group(self):
        terminal_group_code = self.row.get('terminal group code')
        if not isinstance(terminal_group_code, str):
            return {}
        if terminal_group_code.lower().strip() == '':
            return self.teminal_groups
        groups = []
        codes = terminal_group_code.split(',')
        for gr_code in codes:
            code = gr_code.strip().split('=>').pop(0)
            for group in self.teminal_groups:
                if group.get('code') == code:
                    groups.append(group)
        return groups

    def _map_product_data(self, data):
        data_brand = keep_single_spaces(str(data.get('brand', ''))).lower()
        brand = models.Brand.query.filter(
            func.lower(models.Brand.name) == data_brand,
            models.Brand.is_active == 1
        ).first()

        product_type = models.Misc.query.filter(models.Misc.type == 'product_type').first()

        category = self._get_category(data)

        if category:
            default_attribute_set = category.default_attribute_set
            if default_attribute_set:
                self.attribute_set = default_attribute_set
                self.attribute_set_id = default_attribute_set.id

        # only get tax out value if it is passed in the import file
        tax_out = None
        if data.get('vat', None):
            tax_out = models.Tax.query.filter(
                models.Tax.label == data.get('vat', '')
            ).first()

        result = {
            'name': data.get('product name'),
            'categoryId': category.id if category else None,
            'attributeSetId': self.attribute_set_id,
            'brandId': brand.id if brand else None,
            'type': product_type.code if product_type else None,
            'taxInCode': '00',
            'taxOutCode': tax_out.code if tax_out else '',
            'warrantyMonths': 0,
            'warrantyNote': data.get('warranty note'),
            'detailedDescription': "",
            'description': "",
            'isBundle': False
        }

        if data.get('master category'):
            master_category = models.MasterCategory.query.filter(
                models.MasterCategory.code == data.get('master category', '').split('=>').pop(0)
            ).first()
            if master_category:
                result['masterCategoryId'] = master_category.id

        if data.get('model'):
            result['model'] = data.get('model')

        result = {k: v for k, v in result.items() if v is not None}

        return result

    def create_sku(self, sellable_create_signal=True):
        sellable_products = []

        data_variant = {
            'variantId': self.variant.id,
            'partNumber': "",
            'barcode': None,
            'allowSellingWithoutStock': False,
            'manageSerial': False,
            'expiryTracking': False,
        }
        if self.row.get('seller_sku') and self.seller.manual_sku:
            data_variant['sellerSku'] = str(self.row.get('seller_sku'))

        category = self._get_category(self.row)
        data_variant['shippingTypes'] = get_shipping_type_by_category_id(category.id)
        data_variant = {k: v for k, v in data_variant.items() if v is not None}
        sellable_products.append(data_variant)
        data = {
            'productId': self.product.id,
            'sellableProducts': sellable_products
        }
        data = SellableProductsRequest().load(data)
        data.update({'seller_id': current_user.seller_id})
        CreateSellableProductsFromImportValidator.validate(data)
        skus, message = create_sellable_products(data=data, sellable_create_signal=False)
        if len(skus) > 0:
            self.sku = skus[0]
            self.import_price_info()
            self.sku.editing_status_code = 'active'
            models.db.session.flush()
            signals.sellable_create_signal.send(self.sku, ppm_listed_price=True)

    def create_variant_images(self):
        pass

    def import_price_info(self):
        groups = self._get_terminal_group()
        terminal_group_ids = [group.get('id') for group in groups]
        price = self.row.get('price', 0)
        selling_status = 0 if self.row.get('selling status', '').lower() == 'không' else 1
        tax_out_code = self.get_tax_out_code()
        if not tax_out_code:
            tax_out_code = self.get_tax_by_category()
        price_info = models.SellableProductPrice(
            sellable_product_id=self.sku.id,
            selling_price=convert_int_field(price, 0),
            selling_status=selling_status,
            tax_out_code=tax_out_code
        )
        if terminal_group_ids:
            price_info.terminal_group_ids = json.dumps(terminal_group_ids)
        models.db.session.add(price_info)
        models.db.session.flush()

    def get_tax_out_code(self):
        if self.row.get('tax out'):
            tax_out = models.Tax.query.filter(
                models.Tax.label == self.row.get('tax out')
            ).first()
            return tax_out.code if tax_out else None
        return None

    def get_tax_by_category(self):
        if self.category:
            return self.category.tax_out_code
        return ''


@signals.on_create_product_quickly
def on_create_product_quickly(params):
    on_create_product_quickly_task.delay(params, send_environ=True)


@celery.task(queue='create_product_quickly')
def on_create_product_quickly_task(params, environ=None):
    with app.request_context(environ):
        create_product_quickly_task = CreateProductQuicklyTask(
            file_id=params.get('id'),
            cls_importer=ImportProductQuickly

        )
        create_product_quickly_task.run()
