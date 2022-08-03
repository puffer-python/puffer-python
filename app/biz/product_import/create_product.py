import logging
import secrets

from copy import deepcopy
from catalog import models, celery, app
from catalog.biz.product_import.base import save_excel, Importer, read_excel
from catalog.biz.result_import import CreateProductImportCapture, ImportStatus
from catalog.extensions import signals

__author__ = 'Minh.ND'

_logger = logging.getLogger(__name__)


class CreateProductTask:

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
            self.import_process()
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
        list_result = self.convert_result_to_list()
        self.reader.insert(num_of_columns, 'Kết quả', list_result)
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
            import_type = self.get_type_from_reader(self.reader_index[self.idx])
            i = self.reader_index[self.idx]
            self.total_row += 1
            try:
                if import_type == 'don':
                    try:
                        self.import_data_don()
                        models.db.session.commit()
                    except Exception:
                        self.result[i] = 'Dữ liệu có ký tự không hợp lệ. Vui lòng kiểm tra lại'
                if import_type == 'cha':
                    self.import_data_cha_and_con()
                    self.total_row -= 1

                if import_type == 'con':
                    self.result[i] = "Không tìm thấy dòng sản phẩm cha"

                if import_type not in ['don', 'cha', 'con']:
                    self.result[i] = 'Loại sản phẩm chưa hỗ trợ'
            except Exception as e:
                _logger.exception(e)
                self.result[i] = 'File chứa ký tự không hợp lệ hoặc hệ thống gặp lỗi'
            self.idx += 1

    def import_data_don(self):
        i = self.reader_index[self.idx]
        importer = self.cls_importer(data=self.reader.loc[i], process=self.process, import_type='don')
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
            capture.message = str(self.result[i])

    def import_data_cha_and_con(self):
        has_con_failed = False
        i = self.reader_index[self.idx]

        if self.idx + 1 >= len(self.reader_index) or (
                self.idx + 1 < len(self.reader_index) and self.get_type_from_reader(
            self.reader_index[self.idx + 1]) != 'con'):
            self.result[i] = "Không tìm thấy sản phẩm con"
        else:
            parent_row = self.reader.loc[i]
            importer = self.cls_importer(data=self.reader.loc[i], process=self.process, import_type='cha')
            result_import = importer.import_row_cha()
            tag = secrets.token_hex(16)
            if result_import is None:
                self.result[i] = 'Thành công'
                i_CHA = i
                importer.import_type = 'con'

                list_cons = []
                while self.idx + 1 < len(self.reader_index) and self.get_type_from_reader(
                        self.reader_index[self.idx + 1]) == 'con':
                    self.idx += 1
                    self.total_row += 1
                    i = self.reader_index[self.idx]
                    importer.row = self.reader.loc[i]
                    result_import = importer.import_row_con()

                    if result_import is None:
                        self.result[i] = 'Thành công'
                        self.total_row_success += 1
                        if not importer.row.get('sku'):
                            if importer.sku:
                                importer.row['sku'] = importer.sku.sku
                                self.skus[i] = importer.sku.sku
                            else:
                                self.skus[i] = ''
                    else:
                        has_con_failed = True
                        self.result[i] = result_import
                    list_cons.append({
                        'i': i,
                        'result': self.result[i],
                        'row': deepcopy(importer.row),
                        'sku': None if not getattr(importer, 'sku', None) else deepcopy(importer.sku)
                    })

                for con_obj in list_cons:
                    i = con_obj.get('i')
                    importer.row = con_obj.get('row')
                    with CreateProductImportCapture(
                            attribute_set_id=importer.attribute_set_id,
                            parent_row=parent_row,
                            import_id=self.process.id,
                            importer=importer,
                            tag=tag) as capture:
                        capture.product_id = importer.product.id
                        if has_con_failed:
                            if con_obj.get('result') == 'Thành công':
                                self.result[i] = "Một trong các sản phẩm con bị sai"
                                self.total_row_success -= 1
                            capture.status = ImportStatus.FAILURE
                        else:
                            capture.status = ImportStatus.SUCCESS
                        capture.data = importer.row.to_dict()
                        capture.message = str(self.result[i])

                if has_con_failed:
                    # Delete all successful Cons if a Con was failed
                    self.result[i_CHA] = 'Không sản phẩm CON nào được tạo thành công'
                    from catalog.services.products.product import delete_product
                    delete_product(importer.product.id, delete_all_sku=True)
                else:
                    # Send signals of successful Cons to SRM and the last Con to product_detail: to optimize the performance
                    models.db.session.commit()
                    for con_obj in list_cons:
                        signals.sellable_create_signal.send(con_obj.get('sku'), allow_update_product_detail=False)
                    last_sku = list_cons[-1].get('sku', None)
                    if last_sku:
                        signals.sellable_create_signal.send(
                            last_sku, allow_update_product_detail=True, allow_send_to_srm=False)
            else:
                self.result[i] = result_import
                while self.idx + 1 < len(self.reader_index) and self.get_type_from_reader(
                        self.reader_index[self.idx + 1]) == 'con':
                    self.idx += 1
                    self.total_row += 1
                    i = self.reader_index[self.idx]
                    importer.import_type = 'con'
                    importer.row = self.reader.loc[i]
                    with CreateProductImportCapture(
                            attribute_set_id=importer.attribute_set_id,
                            parent_row=parent_row,
                            import_id=self.process.id,
                            importer=importer,
                            tag=tag) as capture:
                        i = self.reader_index[self.idx]
                        self.result[i] = 'Tạo mới sản phẩm cha không thành công'
                        capture.status = ImportStatus.FAILURE
                        capture.message = str(self.result[i])

    def get_type_from_reader(self, index):
        return self.reader.loc[index].astype(str).get('type') \
            .strip().lower() if self.reader.loc[index].astype(str).get('type') else ''

    def skip_blank_lines(self):
        for i in self.reader.index:
            if self.get_type_from_reader(i):
                self.reader_index.append(i)
            else:
                self.result[i] = ''

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


@celery.task(queue='import_product')
def import_product_task(params, environ=None, **kwargs):
    with app.request_context(environ):
        create_product_task = CreateProductTask(
            file_id=params.get('id'),
            cls_importer=Importer
        )
        create_product_task.run()
