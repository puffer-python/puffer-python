# pylint: disable=abstract-class-instantiated

import io
import traceback
import uuid

import pandas
import requests
from flask_login import current_user
from sqlalchemy import func, and_, text
import re

import config
from catalog import models, celery
from catalog.biz.product_import.images import download_from_internet_and_upload_to_the_cloud
from catalog.extensions import signals
from catalog.extensions.exceptions import BadRequestException
from catalog.models import FileImport, db, VariantImage
from catalog.services.products.sellable import get_skus_by_filter
from catalog.utils.lambda_list import LambdaList
from catalog.utils.sql_functions import select_and_insert_json


class ImportUpdateImagesSkus:
    def __init__(self, seller_id, user_email, process, f_stream=None, save_output_at=None):
        self.file_stream = f_stream if f_stream else process.path
        self.seller_id = seller_id
        self.user_email = user_email
        self._process = process
        self.save_output_at = save_output_at
        self.skus = []

    def process(self):
        self._pre_process()
        self._main_process()
        self._after_process()
        return self._result

    def _pre_process(self):
        self._df = pandas.read_excel(self.file_stream, header=2, dtype=str, keep_default_na=False)
        self._process.status = 'processing'
        self._result = [""] * self._df.shape[0]
        self._insert_data = []
        self._dict_image_url_cloud_url = {}

    @staticmethod
    def _can_processable_row(row):
        if row[0] and row[3]:
            return True
        return False

    def _main_process(self):
        self._process.total_row_success = 0
        self._lst_sku_id = []
        lst_sku_in_db = []
        lst_sku_by_row = []
        for index, (args) in self._df.iterrows():
            sku = None
            if self._can_processable_row(args):
                seller_sku = str(args[0]).strip()
                uom_name = str(args[1]).strip()
                uom_ratio = str(args[2]).strip()
                try:
                    sku = get_skus_by_filter(seller_id=self.seller_id,
                                             seller_sku=seller_sku,
                                             uom_name=uom_name,
                                             uom_ratio=uom_ratio,
                                             only_one=True)
                    if sku.id not in self._lst_sku_id:
                        self._lst_sku_id.append(sku.id)
                        lst_sku_in_db.append(sku)
                    else:
                        self._result[index] = 'Đã tồn tại SKU ở dòng trên'
                except BadRequestException as ex:
                    self._result[index] = ex.message
                except Exception as ex:
                    self._result[index] = str(ex)
            lst_sku_by_row.append(sku)

        lst_variant_id = LambdaList(lst_sku_in_db).map(lambda x: x.variant_id).filter(lambda x: x).list()
        lst_variant_id_image_quantity = db.session.query(models.VariantImage.product_variant_id,
                                                         func.count(),
                                                         func.min(models.VariantImage.priority),
                                                         func.max(models.VariantImage.priority)) \
            .filter(and_(models.VariantImage.product_variant_id.in_(lst_variant_id),
                         models.VariantImage.status == 1)) \
            .group_by(models.VariantImage.product_variant_id).all()
        self._dic_variant_id_image_quantity = {}
        for entity in lst_variant_id_image_quantity:
            self._dic_variant_id_image_quantity[entity[0]] = entity

        for index, (args) in self._df.iterrows():
            if self._can_processable_row(args):
                self._process_row(index, lst_sku_by_row[index], str(args[3]), str(args[4]))

    def _process_row(self, index, sku, images, append_first):
        if self._result[index]:
            return

        filter_images = images.strip()
        if sku:
            if sku.variant_id:
                array_images = LambdaList(re.split(',|\n', filter_images)) \
                    .map(lambda x: x.strip()).filter(lambda x: x).list()
                current_image_quantity = self._dic_variant_id_image_quantity.get(sku.variant_id, (0, 0, 0, 0))
                if len(array_images) + current_image_quantity[1] > 36:
                    self._result[index] = 'Biến thể của ảnh không được vượt quá 36'
                else:
                    self._result[index] = ''
                    is_append_first = (append_first == 'YES')
                    init_priority = current_image_quantity[3] + 1 if not is_append_first \
                        else current_image_quantity[2] - len(array_images)
                    has_at_least_1_image = False
                    for image_url in array_images:
                        try:
                            if image_url in self._dict_image_url_cloud_url:
                                cloud_url = self._dict_image_url_cloud_url[image_url]
                            else:
                                cloud_url = download_from_internet_and_upload_to_the_cloud(image_url)
                                self._dict_image_url_cloud_url[image_url] = cloud_url
                            self._insert_data.append(VariantImage(
                                url=cloud_url,
                                status=1,
                                is_displayed=1,
                                created_by=self.user_email,
                                product_variant_id=sku.variant_id,
                                priority=init_priority
                            ))
                            sku.updated_by = self.user_email
                            has_at_least_1_image = True
                            init_priority = init_priority + 1
                        except Exception as ex:
                            if self._result[index]:
                                self._result[index] = self._result[index] + '\r\n' + str(ex)
                            else:
                                self._result[index] = str(ex)
                    if has_at_least_1_image:
                        self._process.total_row_success = self._process.total_row_success + 1
                        self.skus.append(sku.sku)
            else:
                self._result[index] = 'Biến thể của sản phẩm không tồn tại'

    def _after_process(self):
        if self._insert_data:
            db.session.bulk_save_objects(self._insert_data)
        if self.skus:
            for sku in self.skus:
                sellable = models.SellableProduct.query.filter(models.SellableProduct.sku == sku).first()
                signals.sellable_update_signal.send(sellable)
        result_path = self._upload_result()
        self._process.success_path = result_path
        self._process.status = 'done'

    def _upload_result(self):
        self._df.insert(len(self._df.columns), 'Kết quả', self._result, True)
        if self.save_output_at is None:
            out = io.BytesIO()
            with pandas.ExcelWriter(out, engine='xlsxwriter', options={'strings_to_urls': False}) as writer:
                self._df.to_excel(writer, index=None)
            out.seek(0)

            upload_url = config.FILE_API + '/upload/doc'
            resp = requests.post(
                url=upload_url,
                files={'file': (
                    f'{uuid.uuid4()}.xlsx',
                    out,
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                },
            )
            if resp.status_code != 200:
                raise RuntimeError(f'Upload kết quả không thành công.\n{resp.json()}')

            return resp.json().get('url')
        else:
            with pandas.ExcelWriter(self.save_output_at, engine='xlsxwriter', options={'strings_to_urls': False}) \
                    as writer:
                self._df.to_excel(writer, index=None)
            return self.save_output_at


@signals.on_update_images_skus_import
def on_update_images_skus_import2(params):
    update_images_skus.delay(params)


@celery.task()
def update_images_skus(params):
    process = models.FileImport.query.get(params['id'])
    try:
        if not process:
            raise RuntimeError("Cannot find the import to be processed")
        process.status = 'processing'
        models.db.session.commit()
        p = ImportUpdateImagesSkus(seller_id=process.seller_id, user_email=process.created_by, process=process)
        p.process()
        models.db.session.commit()
        update_product_details.delay(p.skus, process.created_by)
    except Exception as ex:
        models.db.session.rollback()
        process.status = 'error'
        process.note = "".join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
        models.db.session.commit()


@celery.task()
def update_product_details(skus, updated_by):
    for sku in skus:
        select_and_insert_json(sku, updated_by)
    pass
