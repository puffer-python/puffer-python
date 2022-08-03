# coding=utf-8
import logging
import random
import string

import pytest

from catalog import models as m
from tests import logged_in_user
from tests.catalog.api import APITestCaseClassScoped
from tests.faker import fake
from catalog import models

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@pytest.mark.session_class
class TerminalSellableProductListTestCase(APITestCaseClassScoped):
    ISSUE_KEY = 'SC-518'

    @pytest.fixture(scope='class', autouse=True)
    def _prepare(self, session_class, populate_on_off_status_class_scope):
        TerminalSellableProductListTestCase.seller = fake.seller()
        TerminalSellableProductListTestCase.products = [fake.product() for _ in range(6)]
        TerminalSellableProductListTestCase.variants = [fake.product_variant(
            product_id=random.choice([product.id for product in TerminalSellableProductListTestCase.products])
        ) for _ in range(30)]
        TerminalSellableProductListTestCase.sellables = [fake.sellable_product(
            variant_id=random.choice([variant.id for variant in TerminalSellableProductListTestCase.variants]),
            seller_id=TerminalSellableProductListTestCase.seller.id
        ) for _ in range(30)]
        TerminalSellableProductListTestCase.user = fake.iam_user(
            seller_id=TerminalSellableProductListTestCase.seller.id)
        TerminalSellableProductListTestCase.terminal = fake.terminal(
            seller_id=TerminalSellableProductListTestCase.user.seller_id,
            sellable_ids=[sellable.id for sellable in TerminalSellableProductListTestCase.sellables]
        )
        TerminalSellableProductListTestCase.status = random.choice(
            m.Misc.query.filter(m.Misc.type == 'on_off_status').all()
        )

    def setUp(self):
        super().setUp()
        self.seller_id = TerminalSellableProductListTestCase.seller.id
        sellable_product_ids = list(map(lambda x: x.id, TerminalSellableProductListTestCase.sellables))
        self.products = TerminalSellableProductListTestCase.products
        self.variant_ids = [variant.id for variant in TerminalSellableProductListTestCase.variants]
        self.sellables = models.db.session.query(models.SellableProduct).filter(
            models.SellableProduct.id.in_(sellable_product_ids)).all()
        self.user = TerminalSellableProductListTestCase.user
        self.terminal_code = TerminalSellableProductListTestCase.terminal.code
        self.terminal_id = TerminalSellableProductListTestCase.terminal.id

    def method(self):
        return 'GET'

    def url(self):
        return f'/sellable_products/terminals/{self.terminal_code}/products'

    def call_api(self, data=None, content_type=None, method=None, url=None):
        with logged_in_user(self.user):
            return super().call_api(data, content_type, method, url)

    def assert_found_one(self, sample, res):
        self.assertEqual(1, len(res))
        self.assertEqual(
            sample.id,
            res[0]['id']
        )

    def _get_terminal_product_status(self, sellable_id, terminal_id):
        terminal_product_data = m.SellableProductTerminal.query.filter(
            m.SellableProductTerminal.sellable_product_id == sellable_id,
            m.SellableProductTerminal.terminal_id == terminal_id
        ).first()
        return m.Misc.query.filter(
            m.Misc.type == 'on_off_status',
            m.Misc.code == terminal_product_data.on_off_status
        ).first()

    @pytest.mark.skip()
    def test_passKeywordSKU__matchExactOneSellableProduct(self):
        sellable = random.choice(self.sellables)
        status = self._get_terminal_product_status(sellable.id, self.terminal_id)
        url = f'{self.url()}?page=1&keyword={sellable.sku}&onOffStatus={status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assert_found_one(sellable, body['result']['skus'])

    def assert_found_list(self, sample, res):
        self.assertEqual(
            sorted(s.id for s in sample),
            sorted(r['id'] for r in res)
        )

    def match_status(self, sellable, terminal_id, status):
        _status = self._get_terminal_product_status(sellable.id, terminal_id)
        return _status.id == status.id

    def filter_with_keyword(self, kw, page, status, terminal_id, page_size=10):
        sorted_list = sorted(
            self.sellables,
            key=lambda s: s.product_variant.product_id
        )
        sellables = [sellable for sellable in sorted_list
                     if (
                             kw in sellable.sku.lower()
                             or kw in sellable.name.lower()
                     ) and self.match_status(sellable, terminal_id, status)]

        return sellables[page:(page + 1) * page_size]

    def _test_get_list_sellables_with_keyword(self, kw, page, status):
        url = f'{self.url()}?page={page + 1}&keyword={kw}&onOffStatus={status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assert_found_list(
            sample=self.filter_with_keyword(
                kw=kw,
                page=page,
                status=status,
                terminal_id=self.terminal_id
            ),
            res=body['result']['skus']
        )

    @pytest.mark.skip()
    def test_passKeyWordSKU__returnListSellableProducts(self):
        page = 0
        kw = random.choice(string.digits)
        self._test_get_list_sellables_with_keyword(
            kw=kw,
            page=page,
            status=self.status
        )

    def test_passKeywordName__returnListSellableProducts(self):
        page = 0
        kw = random.choice(string.ascii_letters).lower()
        self._test_get_list_sellables_with_keyword(
            kw=kw,
            page=page,
            status=self.status
        )

    def test_keywordNotExists__returnEmptyList(self):
        page = 0
        kw = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
        self._test_get_list_sellables_with_keyword(
            kw=kw,
            page=page,
            status=self.status
        )

    def _test_apply_filters(self, ft, el_id, sample, status):
        if isinstance(el_id, list):
            el_id = ",".join(str(el) for el in el_id)
        url = f'{self.url()}?page=1&{ft}={el_id}&onOffStatus={status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)

        if isinstance(sample, list):
            self.assert_found_list(
                sample=sample,
                res=body['result']['skus']
            )
        else:
            self.assert_found_one(
                sample=sample,
                res=body['result']['skus']
            )

    def __update_product(self, sellable, category):
        product = fake.product()
        variant = fake.product_variant(product_id=product.id)
        sellable.product_id = product.id
        sellable.variant_id = variant.id
        fake.product_category(
            product_id=sellable.product_id,
            category_id=category.id,
            created_by='quanglm'
        )

    def test_passCategoryId__returnListSellableProducts(self):
        category = fake.category(seller_id=self.user.seller_id, is_active=True)
        sellable = random.choice(self.sellables)
        self.__update_product(sellable, category)
        self._test_apply_filters(
            ft='category',
            el_id=category.id,
            sample=sellable,
            status=self._get_terminal_product_status(
                sellable_id=sellable.id,
                terminal_id=self.terminal_id
            )
        )

    def test_passMultipleCategoryIds__returnListSellableProducts(self):
        """

        :return:
        """
        sellable1, sellable2 = [
                                   sellable for sellable in self.sellables
                                   if self.match_status(sellable, self.terminal_id, self.status)
                               ][:2]
        category1 = fake.category(seller_id=self.user.seller_id, is_active=True)
        self.__update_product(sellable1, category1)
        category2 = fake.category(seller_id=self.user.seller_id, is_active=True)
        self.__update_product(sellable2, category2)

        self._test_apply_filters(
            ft='category',
            el_id=[category1.id, str(category2.id)],
            sample=[sellable1, sellable2],
            status=self.status
        )

    def test_passCategoryNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&category=45634&onOffStatus={self.status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])

    def test_passSingleBrandFilter__returnExactSellableProduct(self):
        brand = fake.brand()
        sellable = random.choice(self.sellables)
        sellable.brand_id = brand.id
        self._test_apply_filters(
            ft='brand',
            el_id=brand.id,
            sample=sellable,
            status=self._get_terminal_product_status(
                terminal_id=self.terminal_id,
                sellable_id=sellable.id
            )
        )

    def test_passMultipleBrandFilters__returnListSellableProducts(self):
        sellable1, sellable2 = [
                                   sellable for sellable in self.sellables if
                                   self.match_status(sellable, self.terminal_id, self.status)
                               ][:2]
        brand1 = fake.brand()
        sellable1.brand_id = brand1.id
        brand2 = fake.brand()
        sellable2.brand_id = brand2.id
        self._test_apply_filters(
            ft='brand',
            el_id=[brand1.id, brand2.id],
            sample=[sellable1, sellable2],
            status=self.status
        )

    def test_passBrandNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&brand=4564314&onOffStatus={self.status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])

    def test_passSellerNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&seller=4564314&onOffStatus={self.status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])

    def test_passStatusNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&onOffStatus=6996'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])

    def test_notPassStatus__returnInvalidResponse(self):
        url = f'{self.url()}?page=1'
        code, body = self.call_api(url=url)

        self.assertEqual(400, code)

    def test_cannot_see_product_of_another_terminal(self):
        sellable = fake.sellable_product(seller_id=self.user.seller_id)
        terminal = fake.terminal(
            seller_id=self.user.seller_id,
            sellable_ids=[sellable.id]
        )
        status = self._get_terminal_product_status(
            sellable_id=sellable.id,
            terminal_id=terminal.id
        )

        url = f'{self.url()}?page=1&keyword={sellable.sku}&onOffStatus={status.id}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])
