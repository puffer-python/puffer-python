import io
import string

from flask import send_file
from flask_login import current_user
from catalog import utils, models
from catalog.services.imports.template_base import TemplateBase
from catalog.services import seller as seller_service
from catalog.services.attribute_sets.attribute_set import get_default_system_attribute_set


class TemplateService:
    CREATE_PRODUCT = 'create_product'
    CREATE_PRODUCT_BASIC_INFO = 'create_product_basic_info'
    UPDATE_PRODUCT = 'update_product'
    UPDATE_ATTRIBUTE_PRODUCT = 'update_attribute_product'
    UPDATE_EDITING_STATUS = 'update_editing_status'
    UPDATE_PRODUCT_TAG = 'tag_product'
    UPDATE_TERMINAL_GROUPS = 'update_terminal_groups'
    UPDATE_IMAGE_PRODUCTS = 'update_images_skus'
    UPDATE_SEO_INFO = 'update_seo_info'
    UPSERT_PRODUCT_CATEGORY = 'upsert_product_category'
    CREATE_PRODUCT_QUICKLY = 'create_product_quickly'

    @classmethod
    def get_instance(cls, import_type, **kwargs):
        template_service = None
        if import_type == cls.CREATE_PRODUCT:
            template_service = TemplateCreateProduct(import_type, kwargs.get('attribute_set_id'))
        if import_type == cls.CREATE_PRODUCT_BASIC_INFO:
            template_service = TemplateCreateProductBasicInfo(import_type)
        if import_type == cls.UPDATE_ATTRIBUTE_PRODUCT:
            template_service = TemplateUpdateAttribute(import_type, kwargs.get('attribute_set_id'))
        if import_type == cls.UPDATE_PRODUCT:
            template_service = TemplateUpdateProduct(import_type)
        if import_type == cls.UPDATE_EDITING_STATUS:
            template_service = TemplateUpdateEdittingStatus(import_type)
        if import_type == cls.UPDATE_PRODUCT_TAG:
            template_service = TemplateUpdateProductTag(import_type)
        if import_type == cls.UPDATE_TERMINAL_GROUPS:
            template_service = TemplateUpdateTerminalGroups(import_type)
        if import_type == cls.UPDATE_IMAGE_PRODUCTS:
            template_service = TemplateUpdateImageProduct(import_type)
        if import_type == cls.UPDATE_SEO_INFO:
            template_service = TemplateUpdateSeoInfo(import_type)
        if import_type == cls.UPSERT_PRODUCT_CATEGORY:
            template_service = TemplateUpsertProductCategory(import_type, kwargs.get('platform_id'))
        if import_type == cls.CREATE_PRODUCT_QUICKLY:
            template_service = TemplateCreateProductQuickly(import_type)
        return template_service


class TemplateCreateProduct(TemplateBase):
    FILE_TEMPLATE = 'template_create_general_product_v2.0.xlsx'
    VAR_COL_OFFSET = 13
    TITLE_ROW_OFFSET = 5
    NUMBER_OF_DETAIL_INFO_COLUMNS = 10
    NUMBER_OF_SALES_INFO_COLUMNS = 2
    GROUP_TITLE_OFFSET = TITLE_ROW_OFFSET - 1
    TAB_FOR_INPUTTING_DATA = 'Import_SanPham'
    TAB_FOR_SAMPLE_DATA = 'DuLieuMau'

    def __init__(self, import_type, attribute_set_id):
        super().__init__(import_type)
        self.attribute_set_id = attribute_set_id

    def generate_general_product_template(self):
        attributes = self._load_sample_data_attributes(self.attribute_set_id)
        seller = seller_service.get_seller_by_id(current_user.seller_id)
        tab_for_inputting_data = self.wb[self.TAB_FOR_INPUTTING_DATA]

        sample_data = {
            **self._load_sample_data_queries(),
            **self._load_sample_data_attribute_options(attributes)
        }
        self._generate_sample_data_sheet(self.wb[self.TAB_FOR_SAMPLE_DATA], sample_data)

        self._add_column_variation_attribute(tab_for_inputting_data, attributes)
        self._add_column_not_variant_attribute(tab_for_inputting_data, attributes)
        self._add_column_variant_image(tab_for_inputting_data)
        self._add_column_uom(tab_for_inputting_data)

        if seller.get('isAutoGeneratedSKU'):
            self._delete_column_seller_sku(tab_for_inputting_data)

        # The raw template is separate cells one-by-one for easier adding cell.
        # Need to merge all related cells at the end
        self._merge_cells(
            tab_for_inputting_data,
            start_column=self.offset,
            end_column=self.offset + self.n_cols_detail_info - 1,
            copy_cell_at='D4',
            cell_name='Thông tin chi tiết của sản phẩm\nChỉ nhập với loại sản phẩm: DON hoặc CON hoặc COMBO'
        )

        return self.wb

    def send_file(self):
        attribute_set = self._load_sample_data_attribute_set(self.attribute_set_id)
        filename = f'Import_{self.import_type} sp_{utils.convert(attribute_set.name)}.xlsx'
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=filename,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        return res


class TemplateUpsertProductCategory(TemplateBase):
    FILE_TEMPLATE = 'template_import_upsert_product_category.xlsx'
    TAB_FOR_INPUTTING_DATA = 'DuLieuNhap'
    TAB_FOR_SAMPLE_DATA = 'DanhMucNganhHang'

    def __init__(self, import_type, platform_id):
        super().__init__(import_type)
        self.platform_id = platform_id

    def _load_sample_data_queries(self):
        sample_data_queries = {
            **self._load_platform_category_data(self.platform_id),
        }
        return sample_data_queries

    def generate_general_product_template(self):
        sample_data = self._load_sample_data_queries()

        self._generate_sample_data_sheet(
            self.wb[self.TAB_FOR_SAMPLE_DATA], sample_data,
            curr_col=1
        )
        return self.wb

    def send_file(self):
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=self.FILE_TEMPLATE,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        res.headers['Content-Disposition'] = f'attachment; filename="{self.FILE_TEMPLATE}"'
        return res


class TemplateCreateProductBasicInfo(TemplateBase):
    FILE_TEMPLATE = 'template_create_product_basic_info.xlsx'
    VAR_COL_OFFSET = 14
    NUMBER_OF_DETAIL_INFO_COLUMNS = 13
    SKU_COLUMN_AT = 4
    COPY_FROM_CELL = 'B4'
    TAB_FOR_INPUTTING_DATA = 'Import_SanPham'
    TAB_FOR_SAMPLE_DATA = 'DuLieuMau'

    def _delete_column_seller_sku(self, ws):
        ws.delete_cols(self.offset + self.SKU_COLUMN_AT - 1)
        self.n_cols_detail_info -= 1

    def _load_sample_data_queries(self):
        sample_data_queries = {
            **self._load_master_cateogry_data('Danh mục hệ thống'),
            **self._load_category_data(),
            **self._load_attribute_sets_data(with_variant=False),
            **self._load_brand_data(),
            **self._load_unit_data(),
            **self._load_product_type_data(),
            **self._load_tax_data(),
            **self._load_shipping_type_data()
        }
        return sample_data_queries

    def generate_general_product_template(self):
        sample_data = self._load_sample_data_queries()
        self._generate_sample_data_sheet(self.wb[self.TAB_FOR_SAMPLE_DATA], sample_data)

        tab_for_inputting_data = self.wb[self.TAB_FOR_INPUTTING_DATA]

        attribute_set = get_default_system_attribute_set()

        attributes = self._load_sample_data_attributes(attribute_set.id)
        seller = seller_service.get_seller_by_id(current_user.seller_id)

        self._add_column_system_group_attributes(tab_for_inputting_data, attributes)
        if seller.get('isAutoGeneratedSKU'):
            self._delete_column_seller_sku(tab_for_inputting_data)

        # The raw template is separate cells one-by-one for easier adding cell.
        # Need to merge all related cells at the end
        self._merge_cells(
            tab_for_inputting_data,
            start_column=self.offset,
            end_column=self.offset + self.n_cols_detail_info - 1,
            copy_cell_at=f'{string.ascii_uppercase[self.offset - 1]}4'
        )

        return self.wb

    def send_file(self):
        filename = f'Import_{self.import_type} sp_.xlsx'
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=filename,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        return res


class TemplateUpdateProduct(TemplateBase):
    FILE_TEMPLATE = 'template_update_general_product_v3.0.xlsx'
    VAR_COL_OFFSET = 22
    TITLE_ROW_OFFSET = 5
    COPY_FROM_CELL = 'A4'
    GROUP_TITLE_OFFSET = TITLE_ROW_OFFSET - 1
    TAB_FOR_INPUTTING_DATA = 'Update_SanPham'
    TAB_FOR_SAMPLE_DATA = 'DuLieuMau'

    def _load_sample_data_queries(self):
        sample_data_queries = {
            **self._load_category_data(),
            **self._load_master_cateogry_data(),
            **self._load_brand_data(),
            **self._load_unit_data(),
            **self._load_product_type_data(),
            **self._load_tax_data(),
            **self._load_shipping_type_data(),
        }
        return sample_data_queries

    def generate_general_product_template(self):
        sample_data = self._load_sample_data_queries()
        tab_for_inputting_data = self.wb[self.TAB_FOR_INPUTTING_DATA]

        attribute_set = get_default_system_attribute_set()
        if attribute_set:
            attributes = self._load_sample_data_attributes(attribute_set.id)
            self._add_column_system_group_attributes(tab_for_inputting_data, attributes)

        self._generate_sample_data_sheet(
            self.wb[self.TAB_FOR_SAMPLE_DATA], sample_data,
            curr_col=1
        )
        return self.wb

    def send_file(self):
        filename = f'Import_{self.import_type} sp_.xlsx'
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=filename,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        return res


class TemplateUpdateAttribute(TemplateBase):
    FILE_TEMPLATE = 'template_update_attribute_product_v3.0.xlsx'
    VAR_COL_OFFSET = 4
    TITLE_ROW_OFFSET = 5
    NUMBER_OF_DETAIL_INFO_COLUMNS = 9
    NUMBER_OF_SALES_INFO_COLUMNS = 2
    GROUP_TITLE_OFFSET = TITLE_ROW_OFFSET - 1
    TAB_FOR_INPUTTING_DATA = 'Update_SanPham'
    TAB_FOR_SAMPLE_DATA = 'DuLieuMau'

    def __init__(self, import_type, attribute_set_id):
        super().__init__(import_type)
        self.attribute_set_id = attribute_set_id

    def generate_general_product_template(self):
        attributes = self._load_sample_data_attributes(self.attribute_set_id)
        sample_data = self._load_sample_data_attribute_options(attributes)
        tab_for_inputting_data = self.wb[self.TAB_FOR_INPUTTING_DATA]

        self._generate_sample_data_sheet(
            self.wb[self.TAB_FOR_SAMPLE_DATA], sample_data,
            curr_col=1
        )

        self._add_column_not_variant_attribute(
            tab_for_inputting_data, attributes
        )

        return self.wb

    def send_file(self):
        attribute_set = self._load_sample_data_attribute_set(self.attribute_set_id)
        filename = f'Import_{self.import_type} sp_{utils.convert(attribute_set.name)}.xlsx'
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=filename,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        return res


class TemplateUpdateEdittingStatus(TemplateBase):
    FILE_TEMPLATE = 'template_update_status_product.xlsx'


class TemplateUpdateProductTag(TemplateBase):
    FILE_TEMPLATE = 'template_import_update_product_tag.xlsx'


class TemplateUpdateImageProduct(TemplateBase):
    FILE_TEMPLATE = 'template_import_update_images_skus_v3.0.xlsx'


class TemplateUpdateSeoInfo(TemplateBase):
    FILE_TEMPLATE = 'template_import_update_seo_info.xlsx'
    TITLE_ROW_OFFSET = 3


class TemplateUpdateTerminalGroups(TemplateBase):
    FILE_TEMPLATE = 'template_import_update_product_terminal_groups.xlsx'
    TAB_FOR_TERMINAL_GROUP = 'DanhSachNhomDiemBan'
    TAB_FOR_TERMINAL_GROUP_START_ROW = 2

    def generate_general_product_template(self):
        tab_for_terminal_group = self.wb[self.TAB_FOR_TERMINAL_GROUP]

        terminal_groups = models.TerminalGroup.query.filter(
            models.TerminalGroup.is_active == 1, models.TerminalGroup.seller_id == current_user.seller_id).all()

        start_row = self.TAB_FOR_TERMINAL_GROUP_START_ROW
        for tg in terminal_groups:
            name = f'{tg.code}=>{tg.name}'
            tab_for_terminal_group.cell(row=start_row, column=1, value=name)
            start_row += 1

        return self.wb

    def send_file(self):
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=self.FILE_TEMPLATE,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        res.headers['Content-Disposition'] = f'attachment; filename="{self.FILE_TEMPLATE}"'
        return res


class TemplateCreateProductQuickly(TemplateBase):
    FILE_TEMPLATE = 'template_import_create_product_quickly.xlsx'
    TAB_FOR_INPUTTING_DATA = 'Import_SanPham'
    TAB_FOR_SAMPLE_DATA = 'DuLieuMau'

    def _load_sample_data_queries(self):
        from catalog.services.terminal import get_terminal_groups
        terminal_groups = get_terminal_groups(current_user.seller_id)
        terminal_groups = {"Nhóm điểm bán": map(lambda x: f'{x["code"]}=>{x["name"]}', terminal_groups)}
        sample_data_queries = {
            **self._load_category_data(),
            **self._load_brand_data(),
            **self._load_unit_data(),
            **self._load_tax_data(),
            **terminal_groups
        }
        return sample_data_queries

    def generate_general_product_template(self):
        sample_data = self._load_sample_data_queries()

        self._generate_sample_data_sheet(
            self.wb[self.TAB_FOR_SAMPLE_DATA], sample_data,
            curr_col=1
        )
        return self.wb

    def send_file(self):
        out = io.BytesIO()
        self.wb.save(out)
        out.seek(0)
        res = send_file(
            filename_or_fp=out,
            attachment_filename=self.FILE_TEMPLATE,
            mimetype=self.wb.mime_type,
            as_attachment=True
        )
        res.headers['Content-Disposition'] = f'attachment; filename="{self.FILE_TEMPLATE}"'
        return res
