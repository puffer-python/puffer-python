# coding=utf-8
import os
import json
import logging
from tests.faker import fake

from tests.catalog.api import APITestCaseWithMysql
from catalog import models as m, config
from unittest import mock

__author__ = 'Quang.LM'
_logger = logging.getLogger(__name__)


_DATA = '''
{"id": 194635, "sku": "123456", "tax": {"tax_in": 0, "tax_out": null, "tax_in_code": "00", "tax_out_code": null}, "url": "gao-thom-dac-san-st25-neptune", "name": "Gạo Thơm Đặc Sản ST25 Neptune", "tags": [], "type": {"code": "product", "name": "Sản phẩm có thể lưu trữ"}, "brand": {"id": 1382, "code": "neptune", "name": "Neptune", "description": ""}, "color": null, "images": [{"url": "https://lh3.googleusercontent.com/S7cvewSffDTjb0tNJOpJeDAIIM_1wqI6FunbuVMYmobxdvgPLKmVo7nsZDQZWeLpQq5oIR0SfU8g09po1x60wsh2sn_SjJY", "path": "", "label": null, "priority": 1}], "seller": {"id": 2, "name": "CÔNG TY CỔ PHẦN VNPAY SHOP THƯƠNG MẠI DỊCH VỤ", "display_name": "VnPay Shop"}, "status": {"priority": 1, "editing_status": "pending_approval", "publish_status": 0, "need_manage_stock": 1, "selling_status_code": "hang_ban"}, "barcode": "18938516870024", "channels": null, "provider": {"id": 2}, "seo_info": {"meta_title": "", "description": "Gạo Thơm Đặc Sản ST25 Neptune", "meta_keyword": "", "meta_description": "", "short_description": ""}, "uom_code": "54", "warranty": {"months": 0, "description": null}, "is_bundle": 0, "seller_id": 2, "terminals": [], "attributes": [{"id": 1433, "code": "uom", "name": "Đơn vị tính", "values": [{"value": "Gói", "option_id": 13207}], "priority": 1011, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1434, "code": "uom_ratio", "name": "Tỉ lệ quy đổi", "values": [{"value": "1", "option_id": null}], "priority": 1012, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1368, "code": "weight", "name": "Cân nặng", "values": [{"value": null, "option_id": null}], "priority": 1002, "is_comparable": 1, "is_filterable": 0, "is_searchable": 0}, {"id": 1369, "code": "length", "name": "Chiều dài", "values": [{"value": null, "option_id": null}], "priority": 1003, "is_comparable": 1, "is_filterable": 0, "is_searchable": 0}, {"id": 1370, "code": "width", "name": "Chiều rộng", "values": [{"value": "GL Series", "option_id": 26}], "priority": 1004, "is_comparable": 1, "is_filterable": 0, "is_searchable": 0}, {"id": 1371, "code": "height", "name": "Chiều cao", "values": [{"value": null, "option_id": null}], "priority": 1005, "is_comparable": 1, "is_filterable": 0, "is_searchable": 0}, {"id": 1438, "code": "pack_weight", "name": "Cân nặng đóng gói", "values": [], "priority": 1006, "is_comparable": null, "is_filterable": null, "is_searchable": null}, {"id": 1436, "code": "pack_length", "name": "Chiều dài đóng gói", "values": [], "priority": 1007, "is_comparable": null, "is_filterable": null, "is_searchable": null}, {"id": 1435, "code": "pack_width", "name": "Chiều rộng đóng gói", "values": [], "priority": 1008, "is_comparable": null, "is_filterable": null, "is_searchable": null}, {"id": 1437, "code": "pack_height", "name": "Chiều cao đóng gói", "values": [], "priority": 1009, "is_comparable": null, "is_filterable": null, "is_searchable": null}, {"id": 1310, "code": "thucpham_thuonghieu", "name": "Thương hiệu", "values": [{"value": "Neptune", "option_id": null}], "priority": 2, "is_comparable": 1, "is_filterable": 0, "is_searchable": 1}, {"id": 1257, "code": "xuatxu", "name": "Xuất xứ", "values": [{"value": "Việt Nam", "option_id": 11496}], "priority": 3, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1268, "code": "thanhphan_VNshop", "name": "Thành phần", "values": [{"value": "", "option_id": null}], "priority": 4, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1269, "code": "huongdansudung", "name": "Hướng dẫn sử dụng", "values": [{"value": "", "option_id": null}], "priority": 5, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1311, "code": "baoquan_thucpham", "name": "Bảo quản", "values": [{"value": "Bảo quản nơi khô ráo thoáng mát", "option_id": null}], "priority": 6, "is_comparable": 0, "is_filterable": 0, "is_searchable": 1}, {"id": 1260, "code": "khoiluong", "name": "Khối lượng", "values": [{"value": "", "option_id": null}], "priority": 7, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1312, "code": "luuy", "name": "Lưu ý", "values": [{"value": "", "option_id": null}], "priority": 8, "is_comparable": 0, "is_filterable": 0, "is_searchable": 0}, {"id": 1439, "code": "thoihan_sudung", "name": "Thời hạn sử dụng (Tháng)", "values": [{"value": "12", "option_id": null}], "priority": 9, "is_comparable": 0, "is_filterable": 0, "is_searchable": 1}], "categories": [{"id": 60709, "code": "009", "name": "Thực phẩm, bánh kẹo & nước giải khát", "level": 1, "parent_id": null}, {"id": 60747, "code": "009-004", "name": "Đồ khô", "level": 2, "parent_id": 60709}, {"id": 60751, "code": "009-004-004", "name": "Gạo khác", "level": 3, "parent_id": 60747}], "created_at": "2021-07-26 04:52:04.000000", "seller_sku": "210701458", "display_name": "", "product_line": {"code": "009", "name": "Thực phẩm, bánh kẹo & nước giải khát"}, "attribute_set": {"id": 82, "name": "Thực phẩm"}, "product_group": {"id": 327599, "name": "Gạo Thơm Đặc Sản ST25 Neptune", "visible": "individual", "variants": null, "configurations": null}, "parent_bundles": null, "serial_managed": 0, "shipping_types": ["NORMAL"], "smart_showroom": "", "bundle_products": null, "terminal_groups": ["pos365_vnshop_selling", "vietinbank_selling", "vnshop_selling_3app", "vnshop_selling_banking", "vnshop_selling_consumer"], "attribute_groups": [{"id": 4157, "name": "Thông tin sản phẩm", "value": "", "priority": 1, "parent_id": 0}, {"id": null, "name": "Thương hiệu", "value": "Neptune", "priority": 2, "parent_id": 4157}, {"id": null, "name": "Xuất xứ", "value": "Việt Nam", "priority": 3, "parent_id": 4157}, {"id": null, "name": "Thành phần", "value": "", "priority": 4, "parent_id": 4157}, {"id": null, "name": "Hướng dẫn sử dụng", "value": "", "priority": 5, "parent_id": 4157}, {"id": null, "name": "Bảo quản", "value": "Bảo quản nơi khô ráo thoáng mát", "priority": 6, "parent_id": 4157}, {"id": null, "name": "Khối lượng", "value": "", "priority": 7, "parent_id": 4157}, {"id": null, "name": "Lưu ý", "value": "", "priority": 8, "parent_id": 4157}, {"id": null, "name": "Thời hạn sử dụng (Tháng)", "value": "12", "priority": 9, "parent_id": 4157}], "serial_generated": 0, "seller_categories": [{"id": 1813, "code": "009", "name": "Hàng hoá - Thực phẩm", "level": 1, "parent_id": 0}, {"id": 1820, "code": "009-002", "name": "Thực phẩm", "level": 2, "parent_id": 1813}, {"id": 1821, "code": "009-002-001", "name": "Thực phẩm khô", "level": 3, "parent_id": 1820}, {"id": 1828, "code": "009-002-001-002", "name": "Gạo, nếp", "level": 4, "parent_id": 1821}]}
'''


class ProductDetailsV2MigrationTestCase(APITestCaseWithMysql):
    ISSUE_KEY = 'CATALOGUE-613'
    FOLDER = '/Product/DetailV2/Migration'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.patcher = mock.patch('catalog.extensions.sqlalchemy_utils.log.product_log.handle_saving_log')
        call_log = self.patcher.start()
        call_log.return_value = True
        sku = fake.text()
        master_category = fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        )
        category = fake.category(
            seller_id=self.seller.id,
            master_category_id=master_category.id
        )
        fake.sellable_product(sku=sku, category_id=category.id)
        product_detail = m.ProductDetail(sku=sku, data=_DATA, updated_by='quanglm')
        m.db.session.add(product_detail)
        m.db.session.flush()
        m.db.session.commit()
        self.product_detail = product_detail

    def tearDown(self):
        self.patcher.stop()

    def __run_sql(self):
        with open(os.path.join(config.ROOT_DIR, 'catalog', 'utils', 'MIGRATE_PRODUCT_DETAILS_V2.sql'), 'r') as file:
            sql = file.read()
            m.db.engine.execute(sql)

    def test_migrate_success__with_not_existed_sku(self):
        self.__run_sql()
        product_detail_v2 = m.ProductDetailsV2.query.filter(m.ProductDetailsV2.sku == self.product_detail.sku).first()
        self.assertIsNotNone(product_detail_v2)
        self.assertEqual(self.product_detail.updated_by, product_detail_v2.updated_by)
        fields = [
            'seller_sku',
            'uom_code',
            'uom_ratio',
            'seller_id',
            'seller',
            'provider',
            'product_line',
            'name',
            'url',
            'barcode',
            'shipping_types',
            'type',
            'tax',
            'images',
            'display_name',
            'attribute_set',
            'attributes',
            'categories',
            'seller_categories',
            'brand',
            'status',
            'smart_showroom',
            'color',
            'seo_info',
            'warranty',
            'tags',
            'is_bundle',
            'bundle_products',
            'parent_bundles',
            'channels',
            'attribute_groups',
            'product_group',
            'terminals',
            'manufacture',
            'serial_managed',
            'serial_generated',
            'terminal_groups',
            'created_by']
        data = json.loads(_DATA)
        for field in fields:
            if isinstance(data.get(field), dict) or isinstance(data.get(field), list):
                self.assertEqual(json.dumps(data.get(field), ensure_ascii=False)
                                 or '', getattr(product_detail_v2, field) or '')
            else:
                self.assertEqual(data.get(field) or '', getattr(product_detail_v2, field) or '')

    def test_do_nothing__with_existed_sku(self):
        product_detail_v2 = m.ProductDetailsV2(sku=self.product_detail.sku, name='test')
        m.db.session.add(product_detail_v2)
        m.db.session.commit()
        self.__run_sql()
        product_detail_v2 = m.ProductDetailsV2.query.filter(m.ProductDetailsV2.sku == self.product_detail.sku).first()
        self.assertIsNotNone(product_detail_v2)
        self.assertEqual(product_detail_v2.name, 'test')
