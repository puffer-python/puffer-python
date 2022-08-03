# coding=utf-8
import logging
import random
import string
import pytest

from catalog import models
from tests.catalog.api import APITestCaseClassScoped
from tests.faker import fake
from tests import logged_in_user

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@pytest.mark.session_class
class GetListSellableProductTestCase(APITestCaseClassScoped):
    ISSUE_KEY = 'CATALOGUE-669'
    FOLDER = '/Sellable/List'

    @pytest.fixture(scope='class', autouse=True)
    def _prepare(self, session_class):
        GetListSellableProductTestCase.seller = fake.seller()
        GetListSellableProductTestCase.products = [fake.product() for _ in range(6)]
        GetListSellableProductTestCase.variants = [fake.product_variant(
            product_id=random.choice([product.id for product in GetListSellableProductTestCase.products])
        ) for _ in range(30)]
        GetListSellableProductTestCase.sellables = [fake.sellable_product(
            variant_id=random.choice([variant.id for variant in GetListSellableProductTestCase.variants]),
            seller_id=GetListSellableProductTestCase.seller.id
        ) for _ in range(30)]
        for sellable in GetListSellableProductTestCase.sellables:
            fake.product_category(
                product_id=sellable.product_id,
                category_id=sellable.category_id,
                created_by='quanglm'
            )
        GetListSellableProductTestCase.user = fake.iam_user(seller_id=GetListSellableProductTestCase.seller.id)

    def setUp(self):
        super().setUp()
        self.seller_id = GetListSellableProductTestCase.seller.id
        sellable_product_ids = list(map(lambda x: x.id, GetListSellableProductTestCase.sellables))
        self.products = GetListSellableProductTestCase.products
        self.variant_ids = [variant.id for variant in GetListSellableProductTestCase.variants]
        self.sellables = models.db.session.query(models.SellableProduct).filter(
            models.SellableProduct.id.in_(sellable_product_ids)).all()
        self.user = GetListSellableProductTestCase.user

    def url(self):
        return '/sellable_products'

    def method(self):
        return 'GET'

    def assert_found_one(self, sample, res):
        self.assertEqual(1, len(res))
        self.assertEqual(
            sample.id,
            res[0]['id']
        )

    def filter_with_keyword(self, kw, page, page_size):
        sorted_list = sorted(
            self.sellables,
            key=lambda s: s.product_variant.product_id
        )
        sellables = [sellable for sellable in sorted_list
                     if kw.lower() in sellable.sku.lower()
                     or kw.lower() in sellable.name.lower()
                     ]

        return sellables[page:(page + 1) * page_size]

    def assert_found_list(self, sample, res):
        self.assertEqual(
            sorted(s.id for s in sample),
            sorted(r['id'] for r in res)
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

    def call_api(self, data=None, content_type=None, method=None, url=None):
        with logged_in_user(self.user):
            return super().call_api(data, content_type, method, url)

    def _test_get_list_sellables_with_keyword(self, kw, page, page_size=10):
        url = f'{self.url()}?page={page + 1}&keyword={kw}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assert_found_list(
            sample=self.filter_with_keyword(kw=kw, page=page,
                                            page_size=page_size),
            res=body['result']['skus']
        )

    def test_get_list_sellable_with_skus(self):
        skus = ','.join([x.sku for x in self.sellables])
        url = self.url() + f'?skus={skus}&pageSize=50'

        code, body = self.call_api(url=url)

        assert code == 200
        self.assert_found_list(self.sellables, body['result']['skus'])

    def test_passProviderIds__matchExtractOneSellable(self):
        sellable = fake.sellable_product(
            variant_id=random.choice(self.variant_ids),
            seller_id=self.seller_id,
            provider_id=fake.seller_prov().id,
        )
        url = f'{self.url()}?providerIds={sellable.provider_id}'
        code, body = self.call_api(url=url)
        self.assert_found_one(sellable, body['result']['skus'])

    def test_passIds__matchExtractSellables(self):
        sellables = []
        for _ in range(5):
            sellable = fake.sellable_product(
                variant_id=random.choice(self.variant_ids),
                seller_id=self.seller_id,
                provider_id=fake.seller_prov().id,
            )
            sellables.append(sellable)
        ids = ','.join(map(lambda x: str(x.id), sellables))
        url = f'{self.url()}?ids={ids}'
        code, body = self.call_api(url=url)
        self.assert_found_list(sellables, body['result']['skus'])

    def test_passKeywordSKU__matchExactOneSellable(self):
        sellable = random.choice(self.sellables)
        url = f'{self.url()}?page=1&keyword={sellable.seller_sku}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assert_found_one(sellable, body['result']['skus'])

    @pytest.mark.skip(reason="Todo")
    def test_passKeyWordSKU__returnListSellableProducts(self):
        page = 0
        kw = random.choice(string.ascii_letters)
        self._test_get_list_sellables_with_keyword(kw=kw, page=page)

    @pytest.mark.skip(reason="Todo")
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
                res=body['result']['skus']
            )
        else:
            self.assert_found_one(
                sample=sample,
                res=body['result']['skus']
            )

    def test_200_returnListSellableProductsFilteredByCategoryId(self):
        category = fake.category(seller_id=self.seller_id, is_active=True)
        sellable = random.choice(self.sellables)
        self.__update_product(sellable, category)
        self._test_apply_filters(
            ft='categoryIds',
            el_id=category.id,
            sample=sellable
        )

    def test_passCategory__returnListSellableProducts(self):
        category = fake.category(seller_id=self.seller_id, is_active=True)
        sellable = random.choice(self.sellables)
        self.__update_product(sellable, category)
        self._test_apply_filters(
            ft='category',
            el_id=category.id,
            sample=sellable
        )

    def test_200_returnListSellableProductsFilteredByCategoryIds(self):
        [sellable1, sellable2] = random.sample(self.sellables, k=2)
        category1 = fake.category(seller_id=self.seller_id, is_active=True)
        category2 = fake.category(seller_id=self.seller_id, is_active=True)
        self.__update_product(sellable1, category1)
        self.__update_product(sellable2, category2)
        self._test_apply_filters(
            ft='categoryIds',
            el_id=[category1.id, str(category2.id)],
            sample=[sellable1, sellable2]
        )

    def test_passMultipleCategory__returnListSellableProducts(self):
        [sellable1, sellable2] = random.sample(self.sellables, k=2)
        category1 = fake.category(seller_id=self.seller_id, is_active=True)
        category2 = fake.category(seller_id=self.seller_id, is_active=True)
        self.__update_product(sellable1, category1)
        self.__update_product(sellable2, category2)

        self._test_apply_filters(
            ft='category',
            el_id=[category1.id, str(category2.id)],
            sample=[sellable1, sellable2]
        )

    def test_passCategoryNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&category=4564314'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])

    def test_200_returnListSellableProductsFilteredByBrandId(self):
        brand = fake.brand()
        sellable = random.choice(self.sellables)
        sellable.brand_id = brand.id

        self._test_apply_filters(
            ft='brandIds',
            el_id=brand.id,
            sample=sellable
        )

    def test_passSingleBrandFilter__returnExactSellableProduct(self):
        brand = fake.brand()
        sellable = random.choice(self.sellables)
        sellable.brand_id = brand.id
        self._test_apply_filters(
            ft='brand',
            el_id=brand.id,
            sample=sellable
        )

    def test_200_returnListSellableProductsFilteredByBrandIds(self):
        brands = [fake.brand() for _ in range(3)]
        sellables = [fake.sellable_product(
            seller_id=self.seller_id,
            brand_id=random.choice(brands).id
        )]

        self._test_apply_filters(
            ft='brandIds',
            el_id=[brand.id for brand in brands],
            sample=sellables
        )

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

    def test_passBrandNotExists__returnEmptyList(self):
        url = f'{self.url()}?page=1&brand=4564314'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        self.assertEqual([], body['result']['skus'])

    def test_passSingleAttributeSetFilter__returnExactSellableProduct(self):
        attribute_set = fake.attribute_set()
        sellable = random.choice(self.sellables)
        sellable.attribute_set_id = attribute_set.id
        self._test_apply_filters(
            ft='attributeSet',
            el_id=attribute_set.id,
            sample=sellable
        )

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
        self.assertEqual([], body['result']['skus'])

    def filter_sellable_products_with_status(self, status_codes, page,
                                             page_size=10):
        sorted_list = sorted(
            self.sellables,
            key=lambda s: s.product_variant.product_id
        )
        sellables = [sellable for sellable in sorted_list
                     if sellable.selling_status_code in status_codes]

        return sellables[page: (page + 1) * page_size]

    def test_passSellingStatusFilter__returnListSellableProducts(self):
        pass

    def test_passEditingStatusFilter__returnListSelalbleProducts(self):
        pass

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
        self.assertEqual([], body['result']['skus'])

    def test_passTerminalGroupFilter__returnExactSellableProduct(self):
        self.sku_terminal_group = []
        self.terminal_group = fake.terminal_group(seller_id=self.seller_id)
        for i in range(15):
            self.sku_terminal_group.append(
                fake.sellable_product_terminal_group(
                    terminal_group=self.terminal_group,
                    sellable_product=self.sellables[i]
                )
            )

        url = f'{self.url()}?pageSize=30&terminalGroup={self.terminal_group.code}'
        code, body = self.call_api(url=url)

        self.assertEqual(200, code)
        skus = body['result']['skus']
        self.assertEqual(len(skus), 15)


class TestSellableProductProtoFile(GetListSellableProductTestCase):
    def test_passLoadScheme(self):
        sellable = fake.sellable_product(seller_id=self.seller_id)
        from catalog.biz.sellable import SellableUpdateSchema
        data = SellableUpdateSchema().dump(sellable)
        self.assertTrue('shippingTypes' in data)

    def testShippingType(self):
        sellable = fake.sellable_product(seller_id=self.seller_id)
        from catalog.biz.sellable import SellableUpdateSchema
        shipping_type = fake.shipping_type()
        fake.sellable_product_shipping_type(sellable.id, shipping_type.id)
        data = SellableUpdateSchema().dump(sellable)
        self.assertEqual(data.get('shippingTypes'), [shipping_type.code])
