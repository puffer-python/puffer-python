# coding=utf-8

import os
import logging

import flask
from flask import (
    g,
    request,
    send_file,
)
from flask_login import (
    login_required,
    current_user,
)

from catalog.extensions import flask_restplus as fr
from catalog.services.imports import (
    FileImportService,
    TemplateService,
)
from catalog.validators import imports as validators
import config
from . import schema

from catalog.services.imports.file_import import get_static_columns_config
from ... import models


_logger = logging.getLogger(__name__)

import_ns = fr.Namespace(
    name='import',
    path='/import'
)
service = FileImportService.get_instance()


@import_ns.route('/histories', methods=['GET'])
class ImportHistories(fr.Resource):
    @import_ns.expect(schema.FileImportHistoryListParam, location='args')
    @import_ns.marshal_with(schema.FileImportHistoryList)
    @login_required
    def get(self):
        page = g.args.pop('page')
        page_size = g.args.pop('page_size')
        sort_order = g.args.pop('sort_order')
        sort_field = g.args.pop('sort_field')
        validators.ImportHistoryListValidator.validate({'data': g.args})
        histories, total_records = service.get_import_histories(
            g.args, sort_field, sort_order, page, page_size, current_user.seller_id
        )
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'histories': histories
        }


@import_ns.route('/histories/<int:history_id>/items', methods=['GET'])
class ImportHistoriesItems(fr.Resource):
    @import_ns.marshal_with(schema.ImportHistoryItemList)
    @import_ns.expect(schema.ImportHistoryItemParam, location='args')
    @login_required
    def get(self, history_id):
        validators.ImportHistoryValidator.validate({'hid': history_id})
        page = g.args.pop('page')
        page_size = g.args.pop('page_size')
        items, total_records = service.get_history_items(
            g.args, page, page_size, history_id
        )
        file_import = models.FileImport.query.get(history_id)
        column_config = get_static_columns_config(
            file_import.attribute_set_id if file_import else None,
            current_user.seller_id,
            file_import.type if file_import else None
        )
        return {
            'current_page': page,
            'page_size': page_size,
            'total_records': total_records,
            'items': items,
            'column_config': column_config
        }


@import_ns.route('/histories/<int:hid>', methods=['GET'])
class ImportHistory(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    def get(self, hid):
        validators.ImportHistoryValidator.validate({'hid': hid})
        return service.get_history(hid)


@import_ns.route('/retry/<int:hid>', methods=['PATCH'])
class RetryImport(fr.Resource):
    @import_ns.expect(schema.RetryImportRequestBody, location='body')
    @import_ns.marshal_with(schema.RetryImport, as_list=True)
    def patch(self, hid):
        data = flask.g.body
        validators.RetryImportValidator.validate(
            {'hid': hid, 'items': data.get('items'), 'saveOnly': data.get('saveOnly')})
        return service.save_retry_result(hid, data.get('items'), data.get('saveOnly'))


@import_ns.route('', methods=['POST', 'GET'])
class FileImport(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    @import_ns.expect(schema.FileImportParam, location='args')
    def post(self):
        files = request.files
        data = g.args
        platform_id = data.get('platform_id') or request.headers.get('X-PLATFORM-ID')
        data['platform_id'] = platform_id
        return service.import_data(
            files,
            data,
            current_user
        ), 'File được tải lên thành công'

    @import_ns.expect(schema.FileImportParam, location='args')
    @login_required
    def get(self):
        res = None
        type_ = g.args.get('type')
        args = g.args or {}
        platform_id = args.get('platform_id') or request.headers.get('X-PLATFORM-ID')
        args['platform_id'] = platform_id
        template_service = TemplateService.get_instance(
            import_type=type_,
            **args
        )

        if template_service is not None:
            if type_ in ('create_product', 'update_attribute_product'):
                validators.CreateGeneralTemplateValidator.validate({
                    'attribute_set_id': g.args.get('attribute_set_id')
                })
            elif type_ in ('upsert_product_category'):
                validators.UpdateProductCategoryGeneralTemplateValidator.validate({
                    'platform_id': platform_id
                })
            template_service.generate_general_product_template()
            res = template_service.send_file()

        return res


@import_ns.route('/<int:attribute_set_id>', methods=['POST'])
class FileImportOld(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    def post(self, attribute_set_id):
        files = request.files
        validators.UploadFileImportProductValidator.validate({
            'attribute_set_id': attribute_set_id,
            'files': files
        })
        return service.import_product(files.get('file'),
                                      attribute_set_id, current_user), \
               'File được tải lên thành công'


@import_ns.route('/update_product', methods=['POST'])
class UpdateProductImport(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    def post(self):
        files = request.files
        validators.UploadFileUpdateProductValidator.validate({
            'files': files
        })
        return service.import_update_product(files.get('file'), current_user), \
               'File được tải lên thành công'


@import_ns.route('/update_attribute_product', methods=['POST'])
class UpdateAttributeProductImport(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    def post(self):
        files = request.files
        validators.UploadFileUpdateProductValidator.validate({
            'files': files
        })
        return service.import_update_attribute_product(files.get('file'), current_user), \
               'File được tải lên thành công'


@import_ns.route('/editing_status', methods=['POST'])
class UpdateEditingStatusFileImport(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    @login_required
    def post(self):
        files = request.files
        validators.UploadFileUpdateEditingStatusValidator.validate({
            'files': files
        })
        return service.import_update_editing_status(
            files.get('file'), current_user
        ), 'File được tải lên thành công'


@import_ns.route('/update_product_tag', methods=['POST'])
class UpdateProductTagFileImport(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    @login_required
    def post(self):
        files = request.files
        validators.UploadFileUpdateProductTagValidator.validate({
            'files': files
        })
        return service.import_update_product_tag(
            files.get('file'), current_user
        ), 'File được tải lên thành công'


@import_ns.route('/update_product_terminal_groups', methods=['POST'])
class UpdateProductTerminalGroupsFileImport(fr.Resource):
    @import_ns.marshal_with(schema.FileImportHistory)
    @login_required
    def post(self):
        files = request.files
        validators.UploadFileUpdateProductTerminalGroupsValidator.validate({
            'files': files
        })
        return service.import_update_product_terminal_groups(
            files.get('file'), current_user
        ), 'File được tải lên thành công'


@import_ns.route('/editing_status/template', methods=['GET'])
class GetUpdateEditingStatusTemplate(fr.Resource):
    def get(self):
        filepath = os.path.join(
            config.ROOT_DIR,
            'storage',
            'template',
            'template_update_status_product.xlsx'
        )
        res = send_file(filepath, as_attachment=True)
        res.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
        return res


@import_ns.route('/update_product_tag/template', methods=['GET'])
class GetUpdateProductTagTemplate(fr.Resource):
    def get(self):
        filepath = os.path.join(
            config.ROOT_DIR,
            'storage',
            'template',
            'template_import_update_product_tag.xlsx'
        )
        res = send_file(filepath, as_attachment=True)
        res.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
        return res


@import_ns.route('/update_terminal_groups/template', methods=['GET'])
class GetUpdateProductTerminalGroupsTemplate(fr.Resource):
    def get(self):
        filepath = os.path.join(
            config.ROOT_DIR,
            'storage',
            'template',
            'template_import_update_product_terminal_groups.xlsx'
        )
        res = send_file(filepath, as_attachment=True)
        res.headers['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
        return res
