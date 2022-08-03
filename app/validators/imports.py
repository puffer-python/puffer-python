# coding=utf-8
import json
from datetime import datetime

import pandas as pd
from flask_login import current_user

from config import MAX_IMPORT_FILE_PENDING
from catalog import models
from catalog.extensions import exceptions as exc
from catalog.services.extra import ExtraService
from . import Validator


class ImportHistoryListValidator(Validator):
    @staticmethod
    def validate_params(data, obj_id=None):
        """validate_data

        :param data:
        """
        extra_service = ExtraService.get_instance()

        # check start date <= end date
        start_at = data.get('start_at')
        end_at = data.get('end_at')

        if start_at and end_at and start_at > end_at:
            raise exc.BadRequestException('startAt phải trước thời điểm endAt')
        if start_at and start_at > datetime.now().date():
            raise exc.BadRequestException('startAt phải trước thời điểm hiện tại')

        # check wrong status code
        status = data.get('status')
        import_status = models.Misc.query.filter(
            models.Misc.type == 'import_status'
        )
        import_status_set = set(map(lambda x: x.code, import_status))
        if status and not set(status).issubset(import_status_set):
            raise exc.BadRequestException('status không hợp lệ')

        # check wrong type code
        types = data.get('type')
        if types:
            import_types = extra_service.get_extra_info({
                'types': 'import_types'
            }).get('import_types')
            import_types = [el.code for el in import_types]
            for _type in types:
                if _type not in import_types:
                    raise exc.BadRequestException('type không hợp lệ')


class ImportHistoryValidator(Validator):
    @staticmethod
    def validate_id(hid, *args, **kwargs):
        existed = models.db.session.query(models.FileImport.query.filter(
            models.FileImport.id == hid,
            models.FileImport.seller_id == current_user.seller_id,
        ).exists()).scalar()
        if not existed:
            raise exc.BadRequestException('Không tồn tại lịch sử import')


class RetryImportValidator(Validator):
    @staticmethod
    def validate_id(hid, *args, **kwargs):
        existed = models.db.session.query(models.FileImport.query.filter(
            models.FileImport.id == hid,
            models.FileImport.seller_id == current_user.seller_id,
        ).exists()).scalar()
        if not existed:
            raise exc.BadRequestException('Không tồn tại lịch sử import')

    @staticmethod
    def validate_items_id(hid, items, *args, **kwargs):
        if not items:
            raise exc.BadRequestException('Trường items không được để rỗng')
        items_id = [i['id'] for i in items]
        count = models.db.session.query(models.ResultImport).filter(
            models.ResultImport.id.in_(items_id),
            models.ResultImport.import_id == hid,
        ).count()
        if not count or count != len(items_id):
            raise exc.BadRequestException('Tồn tại rows không thuộc import này')


class CreateGeneralTemplateValidator(Validator):
    @staticmethod
    def validate_attribute_set(attribute_set_id, **kwargs):
        attribute_set = models.AttributeSet.query.get(attribute_set_id)
        if not attribute_set:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')


class UpdateProductCategoryGeneralTemplateValidator(Validator):
    @staticmethod
    def validate_platform_id(platform_id, **kwargs):
        if not platform_id:
            raise exc.BadRequestException('Phải chọn sàn trước khi thực hiện tải file mẫu')


class UploadFileValidator(Validator):
    IMPORT_TYPE_CODE = ''
    MAX_FILE_CONCURRENT_UPLOAD = 1
    TITLE_ROW_OFFSET = 1
    DATA_ROW_RANGE = (0, 1000)
    SHEET_NAME = 0
    SHEET_VERSION = 'VERSION'

    @classmethod
    def validate_file(cls, files, **kwargs):
        if len(files.getlist('file')) > cls.MAX_FILE_CONCURRENT_UPLOAD:
            raise exc.BadRequestException(
                f'Chỉ được upload {cls.MAX_FILE_CONCURRENT_UPLOAD} file 1 lần'
            )
        file = files.get('file')
        excel_content_types = (
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        if not file or file.content_type not in excel_content_types:
            raise exc.BadRequestException('Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)')

        total_new = models.FileImport.query.filter(
            models.FileImport.status.in_(('new', 'processing',)),
            models.FileImport.type == cls.IMPORT_TYPE_CODE,
        ).count()
        if total_new >= MAX_IMPORT_FILE_PENDING:
            raise exc.BadRequestException(f'Hệ thống đang bị quá tải số lượng file cần xử lý. Vui lòng thực hiện sau')

        try:
            q = file.stream.read()
            file.stream.seek(0)
            df = pd.read_excel(file, header=cls.TITLE_ROW_OFFSET, sheet_name=cls.SHEET_NAME)
        except:
            raise exc.BadRequestException('Vui lòng chọn file có định dạng .xls hoặc .xlsx (tối đa 1000 sku)')
        if df.shape[0] > cls.DATA_ROW_RANGE[1]:
            raise exc.BadRequestException(
                'Số lượng sản phẩm trong file không được quá 1 nghìn dòng'
            )
        if df.shape[0] == 0:
            raise exc.BadRequestException('File không có dữ liệu')

    @classmethod
    def validate_version(cls, files, **kwargs):
        file = files.get('file')
        if not file:
            return

        meta_data_file = models.Misc.query.filter(
            models.Misc.type == 'import_type',
            models.Misc.code == cls.IMPORT_TYPE_CODE
        ).first()

        if not meta_data_file or not meta_data_file.config:
            return
        db_version = json.loads(meta_data_file.config).get('version')
        if not db_version:
            return

        try:
            df = pd.read_excel(file, sheet_name=cls.SHEET_VERSION, header=None)
            template_version = int(df.iloc[0][0])
        except:
            raise exc.BadRequestException('Mẫu file import của bạn đã cũ. Vui lòng tải lại file mẫu mới để thực hiện')

        if template_version != db_version:
            raise exc.BadRequestException('Mẫu file import của bạn đã cũ. Vui lòng tải lại file mẫu mới để thực hiện')


class UploadFileUpsertProductCategoryValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'upsert_product_category'
    TITLE_ROW_OFFSET = 3
    SHEET_NAME = 'DuLieuNhap'

    @staticmethod
    def validate_platform_id(platform_id, **kwargs):
        if not platform_id:
            raise exc.BadRequestException('Phải chọn sàn trước khi thực hiện import')


class UploadFileProductQuicklyValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'create_product_quickly'
    TITLE_ROW_OFFSET = 6


class UploadFileUpdateSeoInfoValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'update_seo_info'
    TITLE_ROW_OFFSET = 3


class UploadFileUpdateEditingStatusValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'update_editing_status'


class UploadFileUpdateProductTagValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'tag_product'
    TITLE_ROW_OFFSET = 2


class UploadFileUpdateProductTerminalGroupsValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'update_terminal_groups'
    TITLE_ROW_OFFSET = 3
    SHEET_NAME = 'DuLieuNhap'


class UploadFileImportProductValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'create_product'
    SHEET_NAME = 'Import_SanPham'
    TITLE_ROW_OFFSET = 6

    @staticmethod
    def validate_attribute_set_id(attribute_set_id, **kwargs):
        attribute_set = models.AttributeSet.query.get(attribute_set_id)
        if not attribute_set:
            raise exc.BadRequestException('Bộ thuộc tính không tồn tại')


class UploadFileUpdateProductValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'update_product'
    SHEET_NAME = 'Update_SanPham'
    TITLE_ROW_OFFSET = 6


class UploadFileImportProductBasicInfoValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'create_product_basic_info'
    SHEET_NAME = 'Import_SanPham'
    TITLE_ROW_OFFSET = 6


class UploadFileImportUpdateImagesSkusValidator(UploadFileValidator):
    IMPORT_TYPE_CODE = 'update_images_skus'
    SHEET_NAME = 'DuLieuNhap'
    TITLE_ROW_OFFSET = 2
