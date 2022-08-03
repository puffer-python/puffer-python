# coding=utf-8
import io
import random
import string
import pandas as pd
import pytest
import logging

from mock import patch
from tests import logged_in_user
from catalog import models
from tests.faker import fake
from catalog.models import SellableProductSeoInfoTerminal
from tests.catalog.api import APITestCaseClassScoped, APITestCase
from catalog.constants import DIMENSION_ATTRIBUTES_CODES, PACK_CODE_ATTRIBUTES

__logger__ = logging.getLogger(__name__)


@pytest.mark.session_class
class ExportListSellableProductWithSellerSkuTestCase(APITestCaseClassScoped):
    ISSUE_KEY = 'CATALOGUE-544'
    FOLDER = 'Export/SellerSku'

    @pytest.fixture(scope='class', autouse=True)
    def _prepare(self, session_class):
        ExportListSellableProductTestCase.seller = fake.seller()
        ExportListSellableProductTestCase.products = [fake.product() for _ in range(6)]
        ExportListSellableProductTestCase.variants = [fake.product_variant(
            product_id=random.choice([product.id for product in ExportListSellableProductTestCase.products])
        ) for _ in range(30)]
        ExportListSellableProductTestCase.sellables = [fake.sellable_product(
            variant_id=random.choice([variant.id for variant in ExportListSellableProductTestCase.variants]),
            seller_id=ExportListSellableProductTestCase.seller.id
        ) for _ in range(30)]
        ExportListSellableProductTestCase.user = fake.iam_user(seller_id=ExportListSellableProductTestCase.seller.id)

    def setUp(self):
        super().setUp()
        self.seller_id = ExportListSellableProductTestCase.seller.id
        sellable_product_ids = list(map(lambda x: x.id, ExportListSellableProductTestCase.sellables))
        self.products = ExportListSellableProductTestCase.products
        self.variant_ids = [variant.id for variant in ExportListSellableProductTestCase.variants]
        self.sellables = models.db.session.query(models.SellableProduct).filter(
            models.SellableProduct.id.in_(sellable_product_ids)).all()
        self.user = ExportListSellableProductTestCase.user

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'GET'

    def assert_found_one(self, sample, res):
        assert res.shape[0], 1
        self.assertEqual(
            sample.id,
            res.values[0][0]
        )

    def filter_with_keyword(self, kw, page, page_size):
        sorted_list = sorted(
            self.sellables,
            key=lambda s: s.product_variant.product_id
        )
        sellables = [sellable for sellable in sorted_list
                     if kw in sellable.sku.lower()
                     or kw in sellable.name.lower()]

        return sellables[page:(page + 1) * page_size]

    def assert_found_list(self, sample, res):
        self.assertEqual(
            sorted(s.id for s in sample),
            sorted(v[0] for v in res.values)
        )

    def call_api(self, data=None, content_type=None, method=None, url=None):
        with logged_in_user(self.user):
            url = f'{url}&export=1'
            code, body = super().call_api(data, content_type, method, url)
            if code == 200:
                return code, pd.read_excel(io.BytesIO(body), header=1)
            return code, body


@pytest.mark.session_class
class ExportListSellableProductTestCase(APITestCaseClassScoped):
    ISSUE_KEY = 'CATALOGUE-185'

    @pytest.fixture(scope='class', autouse=True)
    def _prepare(self, session_class):
        ExportListSellableProductTestCase.seller = fake.seller()
        ExportListSellableProductTestCase.products = [fake.product() for _ in range(6)]
        ExportListSellableProductTestCase.variants = [fake.product_variant(
            product_id=random.choice([product.id for product in ExportListSellableProductTestCase.products])
        ) for _ in range(30)]
        ExportListSellableProductTestCase.sellables = [fake.sellable_product(
            variant_id=random.choice([variant.id for variant in ExportListSellableProductTestCase.variants]),
            seller_id=ExportListSellableProductTestCase.seller.id
        ) for _ in range(30)]
        ExportListSellableProductTestCase.user = fake.iam_user(seller_id=ExportListSellableProductTestCase.seller.id)

    def setUp(self):
        super().setUp()
        self.seller_id = ExportListSellableProductTestCase.seller.id
        sellable_product_ids = list(map(lambda x: x.id, ExportListSellableProductTestCase.sellables))
        self.products = ExportListSellableProductTestCase.products
        self.variant_ids = [variant.id for variant in ExportListSellableProductTestCase.variants]
        self.sellables = models.db.session.query(models.SellableProduct).filter(
            models.SellableProduct.id.in_(sellable_product_ids)).all()
        self.user = ExportListSellableProductTestCase.user

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'GET'

    def assert_found_one(self, sample, res):
        assert res.shape[0], 1
        self.assertEqual(
            sample.id,
            res.values[0][0]
        )

    def filter_with_keyword(self, kw, page, page_size):
        sorted_list = sorted(
            self.sellables,
            key=lambda s: s.product_variant.product_id
        )
        sellables = [sellable for sellable in sorted_list
                     if kw in sellable.sku.lower()
                     or kw in sellable.name.lower()]

        return sellables[page:(page + 1) * page_size]

    def assert_found_list(self, sample, res):
        self.assertEqual(
            sorted(s.id for s in sample),
            sorted(v[0] for v in res.values)
        )

    def call_api(self, data=None, content_type=None, method=None, url=None):
        with logged_in_user(self.user):
            url = f'{url}&export=1'
            code, body = super().call_api(data, content_type, method, url)
            return code, body

    def _test_get_list_sellables_with_keyword(self, kw, page, page_size=10):
        url = f'{self.url()}?page={page + 1}&keyword={kw}'
        code, body = self.call_api(url=url)
        self.assertEqual(200, code)

    @pytest.mark.skip(reason='SQLite not support')
    def test_passKeywordSKU__matchExactOneSellable(self):
        sellable = random.choice(self.sellables)
        url = f'{self.url()}?page=1&keyword={sellable.sku}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assert_found_one(sellable, body)

    @pytest.mark.skip()
    def test_passKeyWordSKU__returnListSellableProducts(self):
        page = 0
        kw = random.choice(string.digits)
        self._test_get_list_sellables_with_keyword(kw=kw, page=page)

    @pytest.mark.skip()
    def test_passKeywordName__returnListSellableProducts(self):
        page = 0
        kw = random.choice(string.ascii_letters).lower()
        self._test_get_list_sellables_with_keyword(kw=kw, page=page)

    def test_keywordNotExists__returnEmptyList(self):
        page = 0
        kw = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        self._test_get_list_sellables_with_keyword(kw=kw, page=page)

    def _test_apply_filters(self, ft, el_id, sample):
        if isinstance(el_id, list):
            el_id = ",".join(str(el) for el in el_id)
        url = f'{self.url()}?page=1&{ft}={el_id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)

        if isinstance(sample, list):
            self.assert_found_list(
                sample=sample,
                res=body
            )
        else:
            self.assert_found_one(
                sample=sample,
                res=body
            )

    @pytest.mark.skip(reason='SQLite not support')
    def test_passCategoryId__returnListSellableProducts(self):
        category = fake.category(seller_id=self.seller_id, is_active=True)
        sellable = random.choice(self.sellables)
        sellable.category_id = category.id
        self._test_apply_filters(
            ft='category',
            el_id=category.id,
            sample=sellable
        )

    @pytest.mark.skip()
    def test_passMultipleCategoryIds__returnListSellableProducts(self):
        sellable1, sellable2 = [random.choice(self.sellables)
                                for _ in range(2)]
        category1 = fake.category(seller_id=self.seller_id, is_active=True)
        sellable1.category_id = category1.id
        category2 = fake.category(seller_id=self.seller_id, is_active=True)
        sellable2.category_id = category2.id

        self._test_apply_filters(
            ft='category',
            el_id=[category1.id, str(category2.id)],
            sample=[sellable1, sellable2]
        )

    def test_passCategoryNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&category=4564314'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)

    @pytest.mark.skip(reason='SQLite not support')
    def test_passSingleBrandFilter__returnExactSellableProduct(self):
        brand = fake.brand()
        sellable = random.choice(self.sellables)
        sellable.brand_id = brand.id
        self._test_apply_filters(
            ft='brand',
            el_id=brand.id,
            sample=sellable
        )

    @pytest.mark.skip(reason='SQLite not support')
    def test_passMultipleBrandFilters__returnListSellableProducts(self):
        brands = [fake.brand() for _ in range(3)]
        sellables = [fake.sellable_product(
            seller_id=self.seller_id,
            brand_id=random.choice(brands).id
        )]
        self._test_apply_filters(
            ft='brand',
            el_id=[brand.id for brand in brands],
            sample=sellables
        )

    @pytest.mark.skip(reason='SQLite not support')
    def test_passBrandNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&brand=4564314'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual(0, body.shape[0])

    @pytest.mark.skip(reason='SQLite not support')
    def test_passSingleAttributeSetFilter__returnExactSellableProduct(self):
        attribute_set = fake.attribute_set()
        sellable = random.choice(self.sellables)
        sellable.attribute_set_id = attribute_set.id
        self._test_apply_filters(
            ft='attributeSet',
            el_id=attribute_set.id,
            sample=sellable
        )

    @pytest.mark.skip(reason='SQLite not support')
    def test_passMultipleAttributeSetFilter__returnListSellableProducts(self):
        attribute_sets = [fake.attribute_set() for _ in range(3)]
        sellables = [fake.sellable_product(
            seller_id=self.seller_id,
            attribute_set_id=random.choice(attribute_sets).id
        )]
        self._test_apply_filters(
            ft='attributeSet',
            el_id=[attr_set.id for attr_set in attribute_sets],
            sample=sellables
        )

    def test_passAttributeSetNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&attributeSet=4564314'
        code, body = self.call_api(url=url)
        self.assertEqual(200, code)

    def filter_sellable_products_with_status(self, status_codes, page,
                                             page_size=10):
        sorted_list = sorted(
            self.sellables,
            key=lambda s: s.product_variant.product_id
        )
        sellables = [sellable for sellable in sorted_list
                     if sellable.selling_status_code in status_codes]

        return sellables[page: (page + 1) * page_size]

    def test_with_dimension_attributes(self):
        sku = models.SellableProduct.query.first()
        codes = random.choices(DIMENSION_ATTRIBUTES_CODES + PACK_CODE_ATTRIBUTES, k=random.randint(1, 5))
        codes = list(set(codes))
        for code in codes:
            fake.attribute(code=code, variant_id=sku.variant_id)
        url = f'{self.url()}?page=1&skus={sku.sku}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code, body)

    @pytest.mark.skip(reason='SQLite not support')
    def test_passTerminalFilter__returnExactSellableProduct(self):
        sellable = fake.sellable_product(seller_id=self.seller_id)
        terminal = fake.terminal(
            sellable_ids=[sellable.id],
            seller_id=self.seller_id,
            is_active=True
        )

        self._test_apply_filters(
            ft='terminal',
            el_id=terminal.code,
            sample=sellable
        )

    def test_terminalNotExist__returnEmptyList(self):
        url = f'{self.url()}?page=1&terminal=4564314'
        code, body = self.call_api(url=url)
        self.assertEqual(200, code)

    def test_exceedRecords__returnException(self):
        with patch('catalog.services.QueryBase.__len__') as mock_query:
            mock_query.return_value = 50_001
            url = f'{self.url()}?'
            code, body = self.call_api(url=url)

            self.assertEqual(400, code, body)
            self.assertEqual(body.get('message'), 'Có 50001 kết quả, vượt quá 10000 bản ghi')


class ExportListSellableProductSeoInfoTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-995'
    FOLDER = '/Sellable/exportSEOInfo'

    def method(self):
        return 'GET'

    def url(self):
        return '/sellable_products?export=3'

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def setUp(self):
        self.user = fake.iam_user()
        self.sellable_product = [fake.sellable_product(seller_id=self.user.seller_id, terminal_id=0)
                                 for _ in range(2)]

    @pytest.mark.skip(reason='Need to check later')
    def test_exportSEOInfoSuccessfully(self):
        code, body = self.call_api(url=self.url())
        self.assertEqual(code, 200)

        df = pd.read_excel(io.BytesIO(body), header=1)
        self.assertNotEqual(df.shape[0], 0)
        for _, r in df.iterrows():
            seller_sku = str(r[0])
            uom_code = str(r[1])
            uom_ratio = str(r[2])
            display_name = str(r[3])
            meta_title = str(r[4])
            meta_keyword = str(r[5])
            meta_description = str(r[6])
            url_key = str(r[7])

            sellable = models.SellableProduct.query.filter(
                models.SellableProduct.seller_sku == seller_sku
            ).first()
            seo_info = SellableProductSeoInfoTerminal.query.filter_by(
                sellable_product_id=sellable.id,
                terminal_id=0
            ).first()
            self.assertEqual(seller_sku, sellable.seller_sku)
            self.assertEqual(uom_code, sellable.uom_code)
            self.assertIn(uom_ratio, [sellable.uom_ratio, 'nan'])
            self.assertEqual(display_name, seo_info.display_name)
            self.assertEqual(meta_title, seo_info.meta_title)
            self.assertEqual(meta_description, seo_info.meta_description)
            self.assertEqual(meta_keyword, seo_info.meta_keyword)
            self.assertEqual(url_key, seo_info.url_key)
