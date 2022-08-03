# coding=utf-8


from catalog import models
from sqlalchemy import text
from flask_login import current_user
from catalog.utils import keep_single_spaces
from catalog.models import VariantAttribute
from catalog.constants import ATTRIBUTE_TYPE
from catalog.extensions import convert_float_field
from marshmallow.exceptions import ValidationError
from catalog.utils.lambda_list import LambdaList
from catalog.extensions.signals import sellable_update_signal
from catalog.services.attributes import get_or_new_option
from catalog.extensions.exceptions import BaseHTTPException, BadRequestException
from catalog.services.products.sellable import get_skus_by_filter
from catalog.biz.product_import.import_update_product_basic_info import GeneralUpdateImporter, ImportV2Exception, Status


class UpdateProductAttributeImporter(GeneralUpdateImporter):
    SKIP_ROWS = (0, 1, 2, 3, 4, 6)
    SHEET_NAME = 'Update_SanPham'
    RESULT_HEADER = ('seller_sku', 'unit_of_measure', 'uom_ratio', 'Status', 'Message')
    START_ATTRIBUTE_COLUMN_INDEX = 3

    def _load_resource(self):
        """Preload some source data (category, brand, ...) before executor run
        They are used to mapping if executor need
        """
        # preload resource
        self.dic_attr_set_id_variation_attr = {}
        self.need_update_items = []
        attribute_codes = LambdaList(self.df.columns).skip(self.START_ATTRIBUTE_COLUMN_INDEX).list()
        self.attributes = models.Attribute.query.filter(
            models.Attribute.code.in_(attribute_codes)
        ).all()
        invalid_attribute_codes = LambdaList(
            attribute_codes
        ).filter(lambda x: not LambdaList(self.attributes).filter(lambda y: y.code == x).any()).list()
        if invalid_attribute_codes:
            raise BadRequestException(f'Không tồn tại các thuộc tính có mã: '
                                      f'{LambdaList(invalid_attribute_codes).string_join(",")}')

        self.dic_attribute_options = {}
        for attribute in self.attributes:
            if attribute.value_type in [ATTRIBUTE_TYPE.SELECTION, ATTRIBUTE_TYPE.MULTIPLE_SELECT]:
                self.dic_attribute_options[attribute.code] = {}
                for option in attribute.options:
                    lowercase_value = option.value.lower() if isinstance(option.value, str) else option.value
                    self.dic_attribute_options[attribute.code][lowercase_value] = option.id

    def _mapping_data(self, row):
        """Run before main process execute
        Example: Map excel data to normalize format
        """

        seller_sku = str(row.get('seller_sku')).strip()
        uom_name = str(row.get('unit of measure')).strip()
        uom_name = keep_single_spaces(uom_name)
        uom_ratio = str(row.get('uom ratio')).strip()

        if not seller_sku:
            raise BadRequestException('Thiếu thông tin seller sku')

        data = {}

        try:
            sku = get_skus_by_filter(seller_id=current_user.seller_id,
                                     seller_sku=seller_sku,
                                     uom_name=uom_name,
                                     uom_ratio=uom_ratio,
                                     only_one=True)

            data['sku'] = sku
            data['attribute'] = {}
            for attribute in self.attributes:
                attr_value = row.get(attribute.code)
                if attr_value and (attr_value == attr_value):
                    if self.is_variant_attribute(sku.attribute_set_id, attribute):
                        raise BadRequestException(f'Không được sửa thuộc tính biến thể {attribute.code}')
                    elif attribute.value_type == ATTRIBUTE_TYPE.MULTIPLE_SELECT:
                        values = []
                        dict_option = self.dic_attribute_options.get(attribute.code)
                        for x in attr_value.split(','):
                            x = keep_single_spaces(x)
                            lowercase_x = x.lower() if isinstance(x, str) else x
                            if x:
                                if lowercase_x not in dict_option:
                                    new_option = get_or_new_option(x, attribute, auto_commit=False)
                                    dict_option[lowercase_x] = new_option.id

                                values.append(dict_option.get(lowercase_x))
                        value = LambdaList(values).string_join(',')
                    elif attribute.value_type == ATTRIBUTE_TYPE.SELECTION:
                        dict_option = self.dic_attribute_options.get(attribute.code)
                        x = keep_single_spaces(attr_value)
                        lowercase_x = x.lower() if isinstance(x, str) else x
                        if lowercase_x not in dict_option:
                            new_option = get_or_new_option(x, attribute, auto_commit=False)
                            dict_option[lowercase_x] = new_option.id
                        value = dict_option.get(lowercase_x)
                    elif attribute.value_type == ATTRIBUTE_TYPE.NUMBER:
                        value = convert_float_field(attr_value, None)
                    else:
                        value = attr_value.strip()
                    data['attribute'][attribute.id] = value
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

    def _process_data(self, seller_sku, uom_name, uom_ratio, data, **kwarg):
        try:
            if data['attribute']:
                self.need_update_items.append(data)
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
            r_status = Status.ERROR
            r_msg = 'System error'
        else:
            r_status = Status.SUCCESS
            r_msg = None
        finally:
            return seller_sku, uom_name, uom_ratio, r_status, r_msg

    def _after_process_rows(self):
        # Delete old records
        for item in self.need_update_items:
            models.db.session.execute(text('''
                delete from variant_attribute where variant_id = :variant_id and attribute_id in :attribute_ids
            '''), {
                'variant_id': item['sku'].variant_id,
                'attribute_ids': [*item['attribute']]
            })

        # Insert new records
        inserted_item = []
        indexes = []
        self.need_update_items.reverse()
        for item in self.need_update_items:
            for attribute_id in item['attribute']:
                index = '{}_{}'.format(attribute_id, item['sku'].variant_id)
                if index in indexes:
                    continue
                inserted_item.append(VariantAttribute(
                    value=item['attribute'][attribute_id],
                    variant_id=item['sku'].variant_id,
                    attribute_id=attribute_id
                ))
                indexes.append(index)

        if inserted_item:
            models.db.session.bulk_save_objects(inserted_item)
            models.db.session.commit()

        # Send signal
        variant_ids = LambdaList(inserted_item).map(lambda x: x.variant_id).list()
        sellables = models.SellableProduct.query.filter(
            models.SellableProduct.variant_id.in_(variant_ids)
        ).all()
        for sellable in sellables:
            sellable.updated_by = current_user.email
            sellable_update_signal.send(sellable)

    def is_variant_attribute(self, attribute_set_id, attribute):
        if attribute_set_id not in self.dic_attr_set_id_variation_attr:
            self.dic_attr_set_id_variation_attr[attribute_set_id] = self.load_variation_attribute_ids(attribute_set_id)
        return attribute.id in self.dic_attr_set_id_variation_attr[attribute_set_id]

    @staticmethod
    def load_variation_attribute_ids(attribute_set_id):
        return [r['attribute_id'] for r in models.db.session.execute(text('''
            select aga.attribute_id from attribute_groups ag join attribute_group_attribute aga 
                on ag.id = aga.attribute_group_id 
                where ag.attribute_set_id = :attribute_set_id 
                    and aga.is_variation = 1
        '''), {'attribute_set_id': attribute_set_id})]
