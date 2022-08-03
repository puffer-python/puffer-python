# coding=utf-8
import random

from catalog.services.imports.template import TemplateUpdateProduct, TemplateService
from catalog.utils.lambda_list import LambdaList
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from tests.catalog.services.test_get_terminal_groups import TestGetTerminalGroup


class GenerateUpdateBasicProductTemplateWithDimensionTestCase(APITestCase, TestGetTerminalGroup):
    ISSUE_KEY = 'CATALOGUE-1446'
    FOLDER = '/UpdateBasicProductTemplate/Generate'

    def setUp(self):
        self.seller = fake.seller(
            manual_sku=True,
            is_manage_price=True
        )
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.attribute_set = fake.attribute_set()
        self.fake_uom(self.attribute_set)
        self.group = fake.attribute_group(set_id=self.attribute_set.id, system_group=True)

        self.attributes = list()
        for _ in range(random.randint(5, 20)):
            sys_attr = fake.attribute(group_ids=[self.group.id])
            self.attributes.append(sys_attr)

        self.brand = fake.brand()
        self.type = fake.misc(data_type='product_type', name='Sản phẩm')
        self.tax = fake.tax(label='Thuế 10%')
        # self.terminal_group need to fake it

        self.categories = [fake.category(
            is_active=True,
            seller_id=self.user.seller_id
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

    def fake_uom(self, attribute_set):
        uom_attribute_group = fake.attribute_group(set_id=attribute_set.id)
        uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        uom_ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=0
        )

        fake.attribute_option(uom_attribute.id, value='Cái')
        fake.attribute_option(uom_attribute.id, value='Chiếc')
        fake.attribute_option(uom_ratio_attribute.id, value='1')
        fake.attribute_option(uom_ratio_attribute.id, value='2')

    def _assert_dulieumau(self, ws, column_at, expect_title, expect_total_data):
        self.assertEqual(ws['DuLieuMau'][column_at][0].value, expect_title)
        total_data = [x.value for x in ws['DuLieuMau'][column_at] if x.value is not None]
        self.assertEqual(len(total_data)-1, expect_total_data)

    def test_200_return_valid_excel_file(self):
        with logged_in_user(self.user):
            service = TemplateService.get_instance(
                import_type='update_product',
                attribute_set_id=self.attribute_set.id
            )
            wb = service.generate_general_product_template()

            # ___________Import_SanPham____________
            headers = LambdaList(
                wb['Update_SanPham'][service.TITLE_ROW_OFFSET + 1]).take(21 + len(self.attributes)).map(lambda x: x.value).list()
            exp_headers = [
                    'seller_sku',
                    'unit of measure',
                    'uom ratio',
                    'category',
                    'product name',
                    'brand',
                    'model',
                    'warranty months',
                    'warranty note',
                    'vendor tax',
                    'product type',
                    'short description',
                    'description',
                    'part number',
                    'barcode',
                    'allow selling without stock?',
                    'is tracking serial?',
                    'expiry tracking',
                    'expiration type',
                    'days before Exp lock',
                    'shipping type',
                ]
            for attr in self.attributes:
                exp_headers.append(attr.code)
            self.assertListEqual(sorted(exp_headers), sorted(headers))

            self.assertEqual('3', str(wb['VERSION'][1][0].value))

            # ___________DuLieuMau____________
            self._assert_dulieumau(wb, 'A', 'Danh mục ngành hàng', 3)
            self._assert_dulieumau(wb, 'B', 'Danh mục', 2)
            self._assert_dulieumau(wb, 'C', 'Thương hiệu', 1)
            self._assert_dulieumau(wb, 'D', 'Đơn vị tính', 2)
            self._assert_dulieumau(wb, 'E', 'Loại hình sản phẩm', 1)
            self._assert_dulieumau(wb, 'F', 'Thuế suất', 3)
