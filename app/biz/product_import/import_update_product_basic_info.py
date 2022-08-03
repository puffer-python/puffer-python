import io
import uuid
from enum import Enum

import pandas as pd
import requests
from flask_login import current_user
from sqlalchemy import text
from sqlalchemy.orm import load_only
import numpy as np

import config
from catalog import models
from catalog.constants import IMPORT, ATTRIBUTE_TYPE
from catalog.api.product.sellable.schema import UpdateCommonV2RequestBody
from catalog.extensions import convert_int_field
from catalog.extensions.exceptions import BaseHTTPException, BadRequestException
from catalog.services.attribute_sets.attribute_set import get_system_attributes
from catalog.services.attributes import get_or_new_option
from catalog.services.products.sellable import get_skus_by_filter, update_common
from catalog.services.seller import get_default_platform_owner_of_seller
from catalog.services.shipping_types.shipping_type import get_shipping_type_id_by_list_name
from catalog.utils import keep_single_spaces
from catalog.utils.lambda_list import LambdaList
from catalog.validators.sellable import UpdateCommonValidator
from marshmallow.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Status(Enum):
    SUCCESS = 'Success'
    ERROR = 'Error'

    def __str__(self):
        return self.value


class ImportV2Exception(BaseHTTPException):
    def __init__(self, seller_sku=None, uom_name=None, uom_ratio=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.seller_sku = seller_sku
        self.uom_name = uom_name
        self.uom_ratio = uom_ratio


class GeneralUpdateImporter:
    SKIP_ROWS = (0, 1, 2, 3, 4, 6)
    SHEET_NAME = 'Update_SanPham'
    RESULT_HEADER = ('seller_sku', 'unit_of_measure', 'uom_ratio', 'Status', 'Message')

    def __init__(self, task_id):
        self.task_id = task_id
        self.task = None
        self.result = pd.DataFrame(columns=self.RESULT_HEADER, dtype=object)
        self.total_row_success = 0
        self.excel_field_names = []

    def run(self):
        self._fetch_file_import()
        try:
            self._load_resource()
            self._execute()
        except Exception as error:
            self.task.status = 'error'
            self.task.note = str(error)
            models.db.session.commit()

    @staticmethod
    def yes_no_mapping(x=None):
        if x is not None:
            x = str(x)
            if x in ('1', 'Yes'):
                return True
            if x in ('0', 'No'):
                return False

    @staticmethod
    def date_type_mapping(x=None):
        if x is not None:
            x = str(x)
            if x == 'Ngày':
                return 1
            if x == 'Tháng':
                return 2

    def _fetch_file_import(self):
        """Query FileImport for get url excel file"""
        self.task = models.FileImport.query.get(self.task_id)
        if not self.task:
            raise RuntimeError('FileImport not found')
        self.df = pd.read_excel(
            io=self.task.path,
            sheet_name=self.SHEET_NAME,
            skiprows=self.SKIP_ROWS,
            keep_default_na=False,
            dtype=str,
        )
        self.excel_field_names = self.df.columns

    def _execute(self):
        self.task.status = 'processing'
        self.task.total_row_success = 0
        models.db.session.commit()

        try:
            # mapping -> main process -> export result
            for _, row in self.df.iterrows():
                seller_sku, uom_name, uom_ratio = '', '', ''
                try:
                    seller_sku, uom_name, uom_ratio, data = self._mapping_data(row)
                    default_category = False
                    if self.task.type in IMPORT.IMPORT_WITH_DEFAULT_CATEGORY:
                        default_category = True
                    seller_sku, uom_name, uom_ratio, r_status, r_msg = self._process_data(
                        seller_sku, uom_name, uom_ratio, data, default_category=default_category)
                except ImportV2Exception as error:
                    r_status = Status.ERROR
                    r_msg = error.description
                    seller_sku = error.seller_sku
                    uom_name = error.uom_name
                    uom_ratio = error.uom_ratio
                except Exception as ex:
                    _logger.exception(ex)
                    r_status = Status.ERROR
                    r_msg = 'System error'
                finally:
                    self._export_result(seller_sku, uom_name, uom_ratio, r_status, r_msg)
            self._after_process_rows()
        except Exception as error:
            _logger.exception(error)
            self.task.status = 'error'
            self.task.note = str(error)
        else:
            # write and upload file
            file = io.BytesIO()
            self.result.to_excel(file, 'Result', index=False)
            file.seek(0)
            report_url = self.upload_result_to_server(file)

            # update FileImport
            self.task.status = 'done'
            self.task.success_path = report_url
        finally:
            models.db.session.commit()

    @staticmethod
    def upload_result_to_server(file):
        """Upload importing result to file service"""
        upload_form = {'file': (
            f'{uuid.uuid4()}.xlsx',
            file,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )}
        resp = requests.post('{}/upload/doc'.format(config.FILE_API), files=upload_form)
        if resp.status_code != 200:
            raise RuntimeError('Result file can not upload to server')
        return resp.json().get('url')

    def _load_resource(self):
        """Preload some source data (category, brand, ...) before executor run
        They are used to mapping if executor need
        """
        # preload resource
        self.master_category_mapping = []
        self.category_mapping = []
        self.brand_mapping = []
        self.tax_mapping = []
        self.unit_mapping = []

        if 'category' in self.excel_field_names:
            default_platform_owner_id = get_default_platform_owner_of_seller(self.task.seller_id)
            category_codes = self.df['category'].map(lambda x: str(x).split('=>')[0]).drop_duplicates().values
            categories = models.Category.query.filter(
                models.Category.code.in_(category_codes),
                models.Category.seller_id == default_platform_owner_id
            ).options(
                load_only('id', 'code')
            )
            self.category_mapping = {x.code: x.id for x in categories}

        if 'master category' in self.excel_field_names:
            master_category_codes = self.df['master category'].map(
                lambda x: str(x).split('=>')[0]).drop_duplicates().values
            master_categories = models.MasterCategory.query.filter(
                models.MasterCategory.code.in_(master_category_codes)
            ).options(
                load_only('id', 'code')
            )
            self.master_category_mapping = {x.code: x.id for x in master_categories}

        if 'brand' in self.excel_field_names:
            brand_names = [keep_single_spaces(str(value)) for value in self.df['brand'].drop_duplicates().values]
            brands = models.Brand.query.filter(
                models.Brand.name.in_(brand_names)
            ).options(
                load_only('name', 'id')
            )
            self.brand_mapping = {x.name: x.id for x in brands}

        _tax = []
        if 'vendor tax' in self.excel_field_names:
            _tax.append(self.df['vendor tax'].values)
        if 'vat' in self.excel_field_names:
            _tax.append(self.df['vat'].values)
        if _tax:
            tax_labels = np.unique(np.hstack(_tax))
            taxes = models.Tax.query.filter(
                models.Tax.label.in_(tax_labels)
            ).options(
                load_only('label', 'code')
            )
            self.tax_mapping = {x.label: x.code for x in taxes}

    def _mapping_data(self, row):
        """Run before main process execute
        Example: Map excel data to normalize format
        """

        MAPPING_FIELD = {
            'masterCategoryId': ('master category', lambda x: self.master_category_mapping.get(str(x).split('=>')[0])),
            'categoryId': ('category', lambda x: self.category_mapping.get(str(x).split('=>')[0])),
            'name': ('product name', lambda x: str(x) if x is not None else None),
            'brandId': ('brand', lambda x: self.brand_mapping.get(x)),
            'model': ('model', lambda x: str(x) if x is not None else None),
            'warrantyMonths': ('warranty months', convert_int_field),
            'warrantyNote': ('warranty note', lambda x: str(x) if x is not None else None),
            'taxInCode': ('vendor tax', lambda x: self.tax_mapping.get(x)),
            'type': ('product type', lambda x: str(x) if x is not None else None),
            'description': ('short description', lambda x: str(x) if x is not None else None),
            'detailedDescription': ('description', lambda x: str(x) if x is not None else None),
            'partNumber': ('part number', lambda x: str(x) if x is not None else None),
            'barcode': ('barcode', lambda x: str(x) if x is not None else None),
            'allowSellingWithoutStock': ('allow selling without stock?', self.yes_no_mapping),
            'manageSerial': ('is tracking serial?', self.yes_no_mapping),
            'expiryTracking': ('expiry tracking', self.yes_no_mapping),
            'expirationType': ('expiration type', self.date_type_mapping),
            'daysBeforeExpLock': ('days before Exp lock', convert_int_field),
            'shippingTypes': ('shipping type', get_shipping_type_id_by_list_name),
        }

        seller_sku, uom_name = str(row.get('seller_sku')), keep_single_spaces(str(row.get('unit of measure')))
        uom_ratio = str(row.get('uom ratio'))

        if not seller_sku:
            raise BadRequestException('Thiếu thông tin seller sku')

        data = {
            'attribute': {}
        }

        try:
            for target_name, (source_name, map_fn) in MAPPING_FIELD.items():

                if source_name not in self.excel_field_names:
                    continue

                source = row.get(source_name)
                source = str(source).strip() if source is not None else None
                source = keep_single_spaces(source) if source_name == 'brand' else source

                if source not in (None, ''):
                    if map_fn:
                        # pylint: disable=not-callable
                        map_value = map_fn(source)
                        if map_value is None:
                            raise ImportV2Exception(
                                description='Giá trị {} không tồn tại cho {}'.format(source, source_name),
                                seller_sku=seller_sku,
                                uom_name=uom_name,
                                uom_ratio=uom_ratio
                            )
                        data[target_name] = map_value
                    else:
                        data[target_name] = source
                    if data[target_name] in (None, ''):
                        del data[target_name]
            group_attributes = get_system_attributes()
            for group_attr in group_attributes:
                if not group_attr.attribute_group.system_group:
                    continue
                attr = group_attr.attribute
                source = row.get(attr.code)
                source = str(source).strip() if source is not None else None
                data['attribute'][attr.id] = self._get_attribute_value(attr, source)
        except ImportV2Exception as e:
            raise e
        except Exception as e:
            e_wrap = ImportV2Exception(
                seller_sku=seller_sku,
                uom_name=uom_name,
                uom_ratio=uom_ratio,
                description=str(e)
            )
            raise e_wrap
        else:
            return seller_sku, uom_name, uom_ratio, data

    def _add_new_attribute_option(self, dict_option, attr, val):
        if val:
            if val not in dict_option:
                new_option = get_or_new_option(val, attr, auto_commit=False)
                dict_option[val] = new_option.id
            return dict_option[val]

    def _get_attribute_value(self, attr, attr_value):
        if not attr_value:
            return None
        dict_option = {x.value: x.id for x in attr.options}
        if attr.value_type == ATTRIBUTE_TYPE.MULTIPLE_SELECT:
            values = []
            for val in attr_value.split(','):
                val = keep_single_spaces(val)
                val = val.lower() if isinstance(val, str) else val
                val = self._add_new_attribute_option(dict_option, attr, val)
                if val:
                    values.append(val)
            return LambdaList(values).string_join(',')
        if attr.value_type == ATTRIBUTE_TYPE.SELECTION:
            val = keep_single_spaces(attr_value)
            val = val.lower() if isinstance(val, str) else val
            return self._add_new_attribute_option(dict_option, attr, val)
        if attr.value_type == ATTRIBUTE_TYPE.NUMBER:
            try:
                v = float(attr_value)
            except ValueError:
                raise BadRequestException(f'Giá trị thuộc tính {attr.name} phải là số')
            else:
                if attr.is_unsigned and v <= 0:
                    raise BadRequestException(f'Giá trị thuộc tính {attr.name} phải lớn lớn hơn 0')
                return v
        return attr_value.strip()

    def _process_data(self, seller_sku, uom_name, uom_ratio, data, **kwargs):
        try:
            default_category = kwargs.get('default_category', '')
            attributes = data.pop('attribute', [])
            data = UpdateCommonV2RequestBody().load(data)
            sku = get_skus_by_filter(seller_id=current_user.seller_id,
                                     seller_sku=seller_sku,
                                     uom_name=uom_name,
                                     uom_ratio=uom_ratio,
                                     only_one=True)
            data.update({'seller_id': current_user.seller_id})
            UpdateCommonValidator(sku.sku).validate({'data': data}, default_category=default_category)
            self._upsert_attributes(sku.variant_id, attributes)
            update_common(sku=sku.sku, data=data)
        except ImportV2Exception as error:
            r_status = Status.ERROR
            r_msg = error.description
            seller_sku = error.seller_sku
            uom_name = error.uom_name
            uom_ratio = error.uom_ratio
        except (ValidationError, BaseHTTPException) as error:
            r_status = Status.ERROR
            r_msg = str(error)
        except Exception as ex:
            _logger.exception(ex)
            r_status = Status.ERROR
            r_msg = 'System error'
        else:
            r_status = Status.SUCCESS
            r_msg = None
        finally:
            return seller_sku, uom_name, uom_ratio, r_status, r_msg

    def _export_result(self, seller_sku, uom_name, uom_ratio, status, msg):
        task = self.task
        self.result = self.result.append(pd.Series(
            (seller_sku, uom_name, uom_ratio, status, msg), index=self.RESULT_HEADER
        ), ignore_index=True)

        task.total_row_success += status == Status.SUCCESS

    def _after_process_rows(self):
        pass

    def _upsert_attributes(self, variant_id, dic_attributes):
        attribute_ids = []
        for attribute_id, value in dic_attributes.items():
            if value:
                attribute_ids.append(attribute_id)
        if not attribute_ids:
            return

        models.db.session.execute(text('''
            delete from variant_attribute where variant_id = :variant_id and attribute_id in :attribute_ids
        '''), {
            'variant_id': variant_id,
            'attribute_ids': attribute_ids
        })

        inserted_item = []
        for attribute_id, value in dic_attributes.items():
            if value:
                inserted_item.append(models.VariantAttribute(
                    value=value,
                    variant_id=variant_id,
                    attribute_id=attribute_id
                ))

        if inserted_item:
            models.db.session.bulk_save_objects(inserted_item)
