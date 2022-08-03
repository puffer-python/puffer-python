# coding=utf-8
import copy
import logging

from sqlalchemy import func

from ...extensions.flask_cache import cache

_logger = logging.getLogger(__name__)
from collections import ChainMap

import pandas as pd
import requests
from flask import current_app
from flask_login import current_user
from sqlalchemy.orm import load_only
from catalog.extensions import signals
from catalog import utils
from catalog import models
from catalog.extensions import exceptions as exc
from catalog.services import Singleton
from .import_item_query import ImportItemQuery
from .query import ImportHistoryQuery
from catalog.validators import imports as validators
from catalog import models as m
from ..attribute_sets.attribute_set import get_normal_attribute
from catalog.services import seller as seller_sv
from sqlalchemy.orm.attributes import flag_modified

static_column_convert = {
    'brand': lambda x: m.Brand.query.filter(m.Brand.name == x).options(load_only('id')).first().id,
    'category': lambda x: m.Category.query.filter(m.Category.code == x.split('=>')[0]).options(
        load_only('id')).first().id,
    'master category': lambda x: m.MasterCategory.query.filter(m.MasterCategory.code == x.split('=>')[0]).options(
        load_only('id')).first().id,
    'vendor tax': lambda x: m.Tax.query.filter(m.Tax.label == x).options(load_only('id')).first().id,
    'product type': lambda x: m.Misc.query.filter(m.Misc.type == 'product_type', m.Misc.name == x).options(
        load_only('id')).first().id,
    'allow selling without stock?': lambda x: True if 'Yes' else False,
    'is tracking serial?': lambda x: True if 'Yes' else False,
}

static_columns_config = {
    "name": {
        "id": 1,
        "title": "Tên sản phẩm",
        "required": True,
        "valueType": "text"
    },
    "image": {
        "id": 2,
        "title": "Ảnh",
        "required": True,
        "valueType": "text"
    },
    "sku": {
        "id": 3,
        "title": "SKU",
        "required": True,
        "valueType": "text"
    },
    'brand': {
        'id': 4,
        'title': 'Thương hiệu',
        'required': False,
        'valueType': 'selection',
        'options': [],
    },
    'category': {
        'id': 5,
        'title': 'Danh mục',
        'required': True,
        'valueType': 'selection',
        'options': [],
    },
    'master category': {
        'id': 6,
        'title': 'Danh mục ngành hàng',
        'required': False,
        'valueType': 'selection',
        'options': [],
    },
    'vendor tax': {
        'id': 7,
        'title': 'Thuế',
        'required': True,
        'valueType': 'selection',
        'options': [],
    },
    'product type': {
        'id': 8,
        'title': 'Loại sản phẩm',
        'required': True,
        'valueType': 'selection',
        'options': [],
    },
    'allow selling without stock?': {
        'id': 9,
        'title': 'Cho phép bán tồn kho',
        'required': False,
        'valueType': 'selection',
        'options': [True, False],
    },
    'is tracking serial': {
        'id': 11,
        'title': 'Quản lí serial?',
        'required': False,
        'valueType': 'selection',
        'options': [True, False],
    }
}


@cache.memoize(timeout=300)
def get_static_columns_config(attribute_set_id=None, seller_id=None, type=None):
    if type == 'create_product_quickly':
        cols = [
            {'title': 'Seller SKU', 'code': 'seller_sku', 'required': False},
            {'title': 'Tên sản phẩm', 'code': 'product name', 'required': True},
            {'title': 'Danh mục ngành hàng', 'code': 'category', 'required': True},
            {'title': 'Thương hiệu', 'code': 'brand', 'required': True},
            {'title': 'Đơn vị tính', 'code': 'uom', 'required': True},
            {'title': 'Giá bán', 'code': 'price', 'required': False},
            {'title': 'Thuế bán ra', 'code': 'tax out', 'required': False},
            {'title': 'Danh sách Nhóm điểm bán', 'code': 'terminal group code', 'required': False},
            {'title': 'Mở Bán', 'code': 'selling status', 'required': False},
        ]
        static_columns = {}
        for idx, col in enumerate(cols):
            static_columns[col.get('code')] = {
                'id': idx,
                'title': col.get('title'),
                'required': col.get('required', False),
                "valueType": "text",
                "options": []

            }

        return static_columns
    else:
        cols = [
            {'title': 'Loại sản phẩm', 'code': 'type', 'required': True},
            {'title': 'Danh mục hệ thống', 'code': 'master category'},
            {'title': 'Danh mục ngành hàng', 'code': 'category', 'required': True},
            {'title': 'Nhóm sản phẩm', 'code': 'attribute set', 'required': True},
            {'title': 'Tên sản phẩm', 'code': 'product name', 'required': True},
            {'title': 'Thương hiệu', 'code': 'brand', 'required': True},
            {'title': 'Model', 'code': 'model'},
            {'title': 'Thời hạn bảo hành (tháng)', 'code': 'warranty months', 'required': True},
            {'title': 'Ghi chú bảo hành', 'code': 'warranty note'},
            {'title': 'Thuế mua vào', 'code': 'vendor tax', 'required': True},
            {'title': 'Loại hình vận chuyển', 'code': 'shipping type'},
            {'title': 'Loại hình sản phẩm', 'code': 'product type', 'required': True},
            {'title': 'Đặc điểm nổi bật', 'code': 'short description'},
            {'title': 'Mô tả chi tiết', 'code': 'description'},
            {'title': 'Đơn vị tính', 'code': 'uom', 'required': True},
            {'title': 'Tỷ lệ so với đơn vị tính gốc', 'code': 'uom_ratio', 'required': True},
            {'title': 'Ảnh sản phẩm', 'code': 'image urls'},
            {'title': 'Part number', 'code': 'part number'},
            {'title': 'Barcode', 'code': 'barcode'},
            {'title': 'Cho phép bán không tồn kho', 'code': 'allow selling without stock?', 'required': True},
            {'title': 'Quản lý serial', 'code': 'is tracking serial?', 'required': True},
            {'title': 'Quản lý hạn sử dụng', 'code': 'expiry tracking', 'required': True},
            {'title': 'Đơn vị tính hạn sử dụng', 'code': 'expiration type'},
            {'title': 'Được xuất kho trước hạn sử dụng (ngày)', 'code': 'days before Exp lock'},
            {'title': 'Loại hình vận chuyển', 'code': 'shipping type'},
            {'title': 'Nhóm điểm bán', 'code': 'terminal_group'},

        ]
    """

    """
    seller = seller_sv.get_seller_by_id(seller_id)  # type: dict
    static_columns = {}
    if not seller.get('isAutoGeneratedSKU'):
        # If seller manual sku is on then this field is required
        cols.append({'title': 'SKU', 'code': 'sku', 'required': True})
    for idx, col in enumerate(cols):
        static_columns[col.get('code')] = {
            'id': idx,
            'title': col.get('title'),
            'required': col.get('required', False),
            "valueType": "text",
            "options": []

        }

    normal_attributes = {}
    if attribute_set_id:
        for attribute in get_normal_attribute(attribute_set_id):
            normal_attributes[attribute.code] = {
                'id': attribute.id,
                'title': attribute.name,
                'required': False,
                'valueType': 'text',
                'options': [],
            }
    static_columns.update(normal_attributes)
    return static_columns


def create_dynamic_column_config(attribute_code):
    ret = {}
    attributes = m.Attribute.query.join(
        m.AttributeOption,
        m.Attribute.id == m.AttributeOption.attribute_id,
    ).filter(
        m.Attribute.code.in_(attribute_code),
    ).options(load_only(''))

    for attribute in attributes:
        ret[attribute.code] = {}
    return ret


def create_column_config(columns):
    config = {}
    dynamic_columns_config = create_dynamic_column_config(
        columns
    )
    column_config = ChainMap(
        static_columns_config,
        dynamic_columns_config,
    )

    for column in columns:
        _temp_cnf = column_config.get(column)
        if _temp_cnf:

            obj = {**_temp_cnf}
            options_or_getter_options = _temp_cnf.get('options')

            if callable(options_or_getter_options):
                obj['options'] = options_or_getter_options()
            else:
                obj['options'] = options_or_getter_options

            config[column] = obj

    return config


class ImportFile(object):
    TITLE_ROW_OFFSET = 1
    SHEET_NAME = 0
    IMPORT_FILE_TYPE = ''
    AFTER_IMPORT_SIGNAL = None

    def import_file(self, file, user_info, set_id=None, platform_id=None):
        file.seek(0)
        upload_url = current_app.config['FILE_API'] + '/upload/doc'
        resp = requests.post(
            url=upload_url,
            files={'file': (file.filename, file, file.content_type)},
        )
        if resp.status_code != 200:
            raise exc.BadRequestException('Upload file không thành công', errors=resp.json())
        df = pd.read_excel(file, sheet_name=self.SHEET_NAME, header=self.TITLE_ROW_OFFSET)
        import_record = models.FileImport(
            type=self.IMPORT_FILE_TYPE,
            key=utils.random_string(10),
            status='new',
            total_row=df.shape[0],
            attribute_set_id=set_id,
            seller_id=user_info.seller_id,
            platform_id=platform_id,
            created_by=user_info.email,
            name=file.filename,
            path=resp.json().get('url')
        )
        models.db.session.add(import_record)
        models.db.session.commit()

        if self.AFTER_IMPORT_SIGNAL:
            self.AFTER_IMPORT_SIGNAL.send({
                'id': import_record.id,
            })
        return import_record


class ImportFileProduct(ImportFile):
    TITLE_ROW_OFFSET = 6
    SHEET_NAME = 'Import_SanPham'
    IMPORT_FILE_TYPE = 'create_product'
    AFTER_IMPORT_SIGNAL = signals.product_import_signal


class ImportFileProductBasicInfo(ImportFile):
    TITLE_ROW_OFFSET = 6
    SHEET_NAME = 'Import_SanPham'
    IMPORT_FILE_TYPE = 'create_product_basic_info'
    AFTER_IMPORT_SIGNAL = signals.product_basic_info_import_signal


class ImportFileUpdateProduct(ImportFile):
    TITLE_ROW_OFFSET = 6
    SHEET_NAME = 'Update_SanPham'
    IMPORT_FILE_TYPE = 'update_product'
    AFTER_IMPORT_SIGNAL = signals.update_product_import_signal


class ImportFileUpdateAttributeProduct(ImportFile):
    IMPORT_FILE_TYPE = 'update_attribute_product'
    SHEET_NAME = 'Update_SanPham'
    AFTER_IMPORT_SIGNAL = signals.update_attribute_product_import_signal
    TITLE_ROW_OFFSET = 6


class ImportFileUpdateSeoInfo(ImportFile):
    IMPORT_FILE_TYPE = 'update_seo_info'
    AFTER_IMPORT_SIGNAL = signals.product_update_seo_info_import_signal
    SHEET_NAME = 'Update_SanPham'


class ImportFileUpsertProductCategory(ImportFile):
    TITLE_ROW_OFFSET = 3
    IMPORT_FILE_TYPE = 'upsert_product_category'
    AFTER_IMPORT_SIGNAL = signals.upsert_product_category_import_signal
    SHEET_NAME = 'DuLieuNhap'


class ImportFileUpdateEditingStatus(ImportFile):
    IMPORT_FILE_TYPE = 'update_editing_status'
    AFTER_IMPORT_SIGNAL = signals.product_update_editing_status_import_signal
    SHEET_NAME = 'Data'


class ImportFileUpdateProductTag(ImportFile):
    IMPORT_FILE_TYPE = 'tag_product'
    AFTER_IMPORT_SIGNAL = signals.update_product_tag_import_signal
    TITLE_ROW_OFFSET = 2


class ImportFileUpdateProductTerminalGroups(ImportFile):
    IMPORT_FILE_TYPE = 'update_product_terminal_groups'
    AFTER_IMPORT_SIGNAL = signals.update_product_terminal_groups_import_signal
    TITLE_ROW_OFFSET = 3
    SHEET_NAME = 'DuLieuNhap'


class ImportFileUpdateImagesSkus(ImportFile):
    IMPORT_FILE_TYPE = 'update_images_skus'
    AFTER_IMPORT_SIGNAL = signals.update_images_skus_import_signal
    SHEET_NAME = 'DuLieuNhap'
    TITLE_ROW_OFFSET = 2


class ImportCreateProductQuickly(ImportFile):
    IMPORT_FILE_TYPE = 'create_product_quickly'
    AFTER_IMPORT_SIGNAL = signals.create_product_quickly
    SHEET_NAME = 0
    TITLE_ROW_OFFSET = 6


class FileImportService(Singleton):
    def get_import_histories(self, filters, sort_field, sort_order, page, page_size, seller_id):
        query = ImportHistoryQuery().restrict_by_seller(seller_id)
        query.apply_filters(filters)
        if sort_field and sort_order:
            query.sort(sort_field, sort_order)
        total_records = len(query)
        query.pagination(page, page_size)
        return query.all(), total_records

    def get_history(self, hid):
        query = ImportHistoryQuery().restrict_by_seller(current_user.seller_id)
        query.apply_filters({'id': hid})
        return query.first()

    def get_history_items(self, filters, page, page_size, import_id):
        """
        Query for Import History Items
        Required: import_id
        """
        query = ImportItemQuery()
        filters['import_id'] = import_id
        query.apply_filters(filters)
        total_records = len(query)
        query.pagination(page, page_size)
        return query.all(), total_records

    def import_product(self, file, attribute_set_id, user_info, **kwargs):
        """

        :param user_info:
        :param file:
        :param attribute_set_id:
        :return:

        :rtype: m.FileImport
        """
        import_record = ImportFileProduct().import_file(file, user_info, attribute_set_id)

        return import_record

    def import_product_basic_info(self, file, user_info, **kwargs):
        """

               :param user_info:
               :param file:
               :return:

               :rtype: m.FileImport
               """
        import_record = ImportFileProductBasicInfo().import_file(file, user_info)

        return import_record

    def import_update_editing_status(self, file, user_info, **kwargs):
        """

        :param user_info:
        :param file:
        :return:

        :rtype: m.FileImport
        """
        import_record = ImportFileUpdateEditingStatus().import_file(file, user_info)

        return import_record

    def import_update_seo_info(self, file, user_info, **kwargs):
        """

        :param user_info:
        :param file:
        :return:

        :rtype: m.FileImport
        """
        import_record = ImportFileUpdateSeoInfo().import_file(file, user_info)

        return import_record

    def import_upsert_product_category(self, file, user_info, **kwargs):
        import_record = ImportFileUpsertProductCategory().import_file(file, user_info,
                                                                      platform_id=kwargs.get('platform_id'))

        return import_record

    def import_create_product_quickly(self, file, user_info, **kwargs):
        """

        """
        import_record = ImportCreateProductQuickly().import_file(file, user_info)
        return import_record

    def import_update_product_tag(self, file, user_info, **kwargs):
        """

        :param user_info:
        :param file:
        :return:

        :rtype: m.FileImport
        """
        import_record = ImportFileUpdateProductTag().import_file(file, user_info)

        return import_record

    def import_update_product_terminal_groups(self, file, user_info, **kwargs):
        """

        :param user_info:
        :param file:
        :return:

        :rtype: m.FileImport
        """
        import_record = ImportFileUpdateProductTerminalGroups().import_file(file, user_info)

        return import_record

    def import_update_product(self, file, user_info, **kwargs):
        import_record = ImportFileUpdateProduct().import_file(file, user_info)

        return import_record

    def import_update_attribute_product(self, file, user_info, **kwargs):
        import_record = ImportFileUpdateAttributeProduct().import_file(file, user_info)

        return import_record

    @staticmethod
    def import_images_skus(file, user_info, **kwargs):
        import_record = ImportFileUpdateImagesSkus().import_file(file, user_info)
        return import_record

    def import_data(self, files, data, user_info, **kwargs):
        (validator, handle_fn) = self.mapping_import_type(data['type'])
        if not validator or not handle_fn:
            raise exc.BadRequestException('Loại import không tồn tại')

        import_data = {
            'files': files,
            'user_info': user_info
        }

        if data.get('attribute_set_id'):
            import_data['attribute_set_id'] = data.get('attribute_set_id')

        if data.get('platform_id'):
            import_data['platform_id'] = data.get('platform_id')

        validator.validate(import_data)

        import_data['file'] = files.get('file')
        del import_data['files']

        return handle_fn(**import_data)

    def mapping_import_type(self, import_type):
        mapping_import_type = {
            'create_product': (validators.UploadFileImportProductValidator, self.import_product),
            'create_product_basic_info': (
                validators.UploadFileImportProductBasicInfoValidator,
                self.import_product_basic_info
            ),
            'tag_product': (validators.UploadFileUpdateProductTagValidator, self.import_update_product_tag),
            'update_editing_status': (
                validators.UploadFileUpdateEditingStatusValidator, self.import_update_editing_status),
            'update_product': (validators.UploadFileUpdateProductValidator, self.import_update_product),
            'update_terminal_groups': (
                validators.UploadFileUpdateProductTerminalGroupsValidator, self.import_update_product_terminal_groups),
            'update_attribute_product': (
                validators.UploadFileUpdateProductValidator, self.import_update_attribute_product),
            'update_images_skus': (
                validators.UploadFileImportUpdateImagesSkusValidator, self.import_images_skus),
            'update_seo_info': (
                validators.UploadFileUpdateSeoInfoValidator, self.import_update_seo_info),
            'upsert_product_category': (
                validators.UploadFileUpsertProductCategoryValidator, self.import_upsert_product_category),
            'create_product_quickly': (
                validators.UploadFileProductQuicklyValidator, self.import_create_product_quickly)
        }

        return mapping_import_type.get(import_type, (None, None))

    def save_retry_result(self, import_id, items, save_only):
        """
        loop over the items
        update the new_data of item in database
        commit at the end of loop
        :param items:
        :return:
        """
        result = []
        items_dict = {}
        item_ids = set()
        for i in items:
            items_dict[i['id']] = i.get('data')
            item_ids.add(i['id'])
        histories = m.ResultImport.query.filter(
            models.ResultImport.id.in_(item_ids)
        ).all()

        import_record = m.FileImport.query.get(import_id)
        from catalog.biz.product_import.base import get_all_terminals
        setattr(import_record, 'terminal_groups', get_all_terminals(import_record.seller_id))
        if not import_record:
            raise exc.BadRequestException("Cannot find import")

        for h in histories:
            new_data = copy.deepcopy(h.data)
            new_data.update(items_dict[h.id])
            h.data = new_data

            r = {
                "id": h.id,
                "status": "SUCCESS",
                "message": "successful"
            }
            if not save_only:
                try:
                    self.retry_single_item(import_record, h)
                except Exception as e:
                    _logger.exception(e)
                    r['status'] = "FAILURE"
                    r['message'] = str(e)
            result.append(r)
        delattr(import_record, 'terminal_groups')
        m.db.session.commit()
        return result

    def retry_single_item(self, import_record, retry_item):
        """
        load result data from reult_id
        create an Importer object from the data that has been saved to database
        excute Importer functions for creating product
        save the log
        :param import_record m.FileImport:
        :param retry_item m.ResultImport:
        :return:
        """
        from catalog.biz.result_import import ImportStatus
        from catalog.biz.product_import.base import Importer
        from catalog.biz.product_import.create_product_quickly import ImportProductQuickly
        from catalog.biz.product_import.create_product_basic_info import CreateProductBasicInfoImporter

        type_to_importer_cls = {
            'create_product': Importer,
            'create_product_basic_info': CreateProductBasicInfoImporter,
            'create_product_quickly': ImportProductQuickly
        }

        if not type_to_importer_cls.get(import_record.type):
            raise Exception("Invalid import type to retry")

        if retry_item:
            # build Importer object from data
            import pandas
            row = pandas.DataFrame.from_records([retry_item.data]).loc[0]
            importer = type_to_importer_cls.get(import_record.type)(data=row, process=import_record,
                                                                    import_type=retry_item.data.get('type'))

            if import_record.type == 'create_product_quickly':
                result_import = importer.import_row_don()

            if retry_item.data.get('type', '').lower() == 'don':
                result_import = importer.import_row_don()
            if retry_item.data.get('type', '').lower() == 'con':
                previous_success_row = m.ResultImport.query.filter(
                    m.ResultImport.tag == retry_item.tag,
                    m.ResultImport.product_id > 0
                ).first()
                result_import_cha = None
                if not previous_success_row:
                    importer.import_type = 'cha'
                    result_import_cha = importer.import_row_cha()
                    if not result_import_cha:
                        retry_item.product_id = importer.product.id
                    else:
                        retry_item.message = result_import_cha
                        retry_item.status = ImportStatus.FAILURE
                else:
                    importer.init_attributes()
                    retry_item.product_id = previous_success_row.product_id
                    importer.product = m.Product.query.get(retry_item.product_id)
                    base_uom_variant = m.db.session.query(
                        func.min(m.ProductVariant.id).label("base_uom")
                    ).filter(m.ProductVariant.product_id == retry_item.product_id).one()
                    importer.base_uom = base_uom_variant.base_uom
                if not result_import_cha:
                    importer.import_type = 'con'
                    _logger.info("Base uom when retrying variants: %s" % importer.base_uom)
                    result_import = importer.import_row_con()
                else:
                    result_import = result_import_cha

            if result_import is None:
                import_record.total_row_success = import_record.total_row_success + 1
                retry_item.status = ImportStatus.SUCCESS
                retry_item.data['sku'] = importer.sku.sku
                flag_modified(retry_item, 'data')
            else:
                retry_item.status = ImportStatus.FAILURE

            if result_import is None:
                retry_item.message = 'Thành công'
            else:
                retry_item.message = str(result_import)

            if result_import:
                raise Exception(str(result_import))
            # excute the importer function
            # save the log based on result
