# coding=utf-8
from unittest.mock import patch

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.imports import TemplateService
from catalog import models
from tests import logged_in_user


class GetCreateProductBasicInfoTemplate(APITestCase):
    ISSUE_KEY = 'CATALOGUE-346'
    FOLDER = '/Import/GetCreateProductBasicInfoTemplate'

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.attribute_set = self.fake_attribute_set(is_variation=False)
        self.system_attributes = self.fake_system_attribute(self.attribute_set)

        self.brand = fake.brand()
        self.type = fake.misc(data_type='product_type', name='Sản phẩm')
        self.tax = fake.tax(label='Thuế 10%')
        self.product_type = fake.misc(data_type='product_type')

        self.categories = [fake.category(
            is_active=True,
            seller_id=self.user.seller_id,
            attribute_set_id=self.attribute_set.id
        ) for _ in range(2)]

        self.default_platform_owner = fake.seller()
        platform_id = fake.integer()
        fake.platform_sellers(
            platform_id=platform_id,
            seller_id=self.seller.id,
            is_default=True
        )
        fake.platform_sellers(
            platform_id=platform_id,
            seller_id=self.default_platform_owner.id,
            is_owner=True
        )

        self.default_categories = [fake.category(
            is_active=True,
            seller_id=self.default_platform_owner.id,
            attribute_set_id=self.attribute_set.id
        ) for _ in range(3)]

        self.master_categories = [fake.master_category(
            is_active=True,
            attribute_set_id=self.attribute_set.id
        ) for _ in range(2)]

        self.patcher_seller = patch('catalog.services.seller.get_seller_by_id')
        self.mock_seller = self.patcher_seller.start()
        self.mock_seller.return_value = {
            'isAutoGeneratedSKU': False,
        }

    def tearDown(self):
        self.patcher_seller.stop()

    def fake_attribute_set(self, is_variation=True):
        attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(
            set_id=attribute_set.id, system_group=False)
        attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        fake.attribute_option(attributes[0].id, value='Vàng')
        fake.attribute_option(attributes[0].id, value='Đỏ')
        fake.attribute_option(attributes[1].id, value='S')
        fake.attribute_option(attributes[1].id, value='XXL')

        fake.attribute_group_attribute(attribute_id=attributes[0].id, group_ids=[attribute_group.id], is_variation=is_variation)
        fake.attribute_group_attribute(attribute_id=attributes[1].id, group_ids=[attribute_group.id], is_variation=is_variation)

        return attribute_set

    def fake_system_attribute(self, attribute_set):
        system_group = fake.attribute_group(
            set_id=attribute_set.id, system_group=True, level=1)
        dimemsion_group = fake.attribute_group(
            parent_id=system_group.id, set_id=attribute_set.id, system_group=True, level=2)
        packed_dimemsion_group = fake.attribute_group(
            parent_id=system_group.id, set_id=attribute_set.id, system_group=True, level=2)

        system_attributes = []
        for _ in range(4):
            system_attributes.append(fake.attribute(
                group_ids=[dimemsion_group.id],
                value_type='number'
            ))

        for _ in range(4):
            system_attributes.append(fake.attribute(
                group_ids=[packed_dimemsion_group.id],
                value_type='number'
            ))

        return system_attributes

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(set_id=attribute_set.id, system_group=True)
        uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=True
        )
        uom_ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=False
        )

        fake.attribute_option(uom_attribute.id, value='Cái')
        fake.attribute_option(uom_attribute.id, value='Chiếc')
        fake.attribute_option(uom_ratio_attribute.id, value='1')
        fake.attribute_option(uom_ratio_attribute.id, value='2')

    def _assert_dulieumau(self, template, column_at, expect_title, expect_total_data):
        self.assertEqual(template['DuLieuMau'][column_at][0].value, expect_title)
        total_data = [x.value for x in template['DuLieuMau'][column_at] if x.value is not None]
        self.assertEqual(len(total_data)-1, expect_total_data)

    def test_200_returnValidExcelFile(self):
        """
        In Import_SanPham tab, need to check:
            - attribute_set column
            - the group of system_attribute columns

        In DuLieuMau tab, need to check:
            - type: CHA CON DON
            - categories
            - master_categories
            - attribute_set
            - brand
            - uom value
            - product_type
            - tax
        """

        self.fake_uom(self.attribute_set)

        with logged_in_user(self.user):
            service = TemplateService.get_instance(import_type='create_product_basic_info')
            offset = service.VAR_COL_OFFSET

            wb = service.generate_general_product_template()
            # ___________Import_SanPham____________
            system_attribute_names = [attribute.display_name for attribute in self.system_attributes]

            for idx in range(len(system_attribute_names)):
                attribute_col = wb['Import_SanPham'][service.TITLE_ROW_OFFSET][offset + idx - 1]
                self.assertIn(attribute_col.value, system_attribute_names)
                self.assertNotEqual(attribute_col.font.color.rgb, 'FFFF0000')

            sku_col = wb['Import_SanPham'][service.TITLE_ROW_OFFSET][
                    offset + len(system_attribute_names) - 1 + service.SKU_COLUMN_AT - 1]
            self.assertEqual(sku_col.value.lower(), 'seller sku')
            self.assertEqual(sku_col.font.color.rgb, 'FFFF0000')

            # ___________DuLieuMau____________
            self._assert_dulieumau(wb, 'A', 'Loại sản phẩm', 3)
            self._assert_dulieumau(wb, 'B', 'Danh mục hệ thống', 2)
            self._assert_dulieumau(wb, 'C', 'Danh mục ngành hàng', 3)
            self._assert_dulieumau(wb, 'D', 'Nhóm sản phẩm', 1)
            self._assert_dulieumau(wb, 'E', 'Thương hiệu', 1)
            self._assert_dulieumau(wb, 'F', 'Đơn vị tính', 3)
            self._assert_dulieumau(wb, 'G', 'Loại hình sản phẩm', 2)
            self._assert_dulieumau(wb, 'H', 'Thuế suất', 3)
            self._assert_dulieumau(wb, 'I', 'Loại hình vận chuyển', 0)
            self.assertIsNone(wb['DuLieuMau']['J'][0].value)

    def test_200_notManagePriceColumn(self):
        self.mock_seller.return_value = {
            'isAutoGeneratedSKU': False,
            'usingGoodsManagementModules': True
        }
        with logged_in_user(self.user):
            service = TemplateService.get_instance(import_type='create_product_basic_info')
            wb = service.generate_general_product_template()
            n = len(wb['Import_SanPham'][service.TITLE_ROW_OFFSET])
            for i in range(1, n):
                col_value = wb['Import_SanPham'][service.TITLE_ROW_OFFSET][i].value
                if col_value:
                    assert 'Giá niêm yết' not in col_value

    def test_200_notManualSKU(self):
        self.mock_seller.return_value = {
            'isAutoGeneratedSKU': True,
        }
        with logged_in_user(self.user):
            service = TemplateService.get_instance(import_type='create_product_basic_info')
            wb = service.generate_general_product_template()
            n = len(wb['Import_SanPham'][service.TITLE_ROW_OFFSET])
            for i in range(1, n):
                col_value = wb['Import_SanPham'][service.TITLE_ROW_OFFSET][i].value
                if col_value:
                    assert not col_value.lower() == 'seller sku'

    def test_200_notGenerateAttributeSetWithIsVariantAttribute(self):
        attribute_set = self.fake_attribute_set(is_variation=True)
        self.fake_uom(attribute_set)
        self.fake_system_attribute(attribute_set)

        attribute_set = self.fake_attribute_set(is_variation=False)
        self.fake_uom(attribute_set)
        self.fake_system_attribute(attribute_set)

        with logged_in_user(self.user):
            service = TemplateService.get_instance(import_type='create_product_basic_info')
            offset = service.VAR_COL_OFFSET
            wb = service.generate_general_product_template()

            self.assertEqual(
                wb['Import_SanPham'][service.TITLE_ROW_OFFSET][
                    offset + len(self.system_attributes) - 1 + service.SKU_COLUMN_AT - 1
                ].value.lower(),
                'seller sku'
            )

            self._assert_dulieumau(wb, 'D', 'Nhóm sản phẩm', 2)

