# coding=utf-8
import datetime
import logging
import random
from copy import deepcopy

from flask_login import current_user

from catalog import models
from catalog.models import SellableProductBundle, db
from catalog.utils import camel_case
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class GetSellableProductTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-76'

    def setUp(self):
        self.variant = fake.product_variant()
        self.sellable = fake.sellable_product(variant_id=self.variant.id, seller_id=1)
        self.user = fake.iam_user(seller_id=1)
        self.attributes = [fake.attribute(self.variant.id)
                           for _ in range(6)]
        variant_attr = models.Attribute.query.join(
            models.VariantAttribute,
            models.VariantAttribute.attribute_id == models.Attribute.id
        ).filter(
            models.Attribute.code == 'uom',
            models.VariantAttribute.variant_id == self.variant.id
        ).first()

        self.attributes.append(variant_attr)

        self.images = [fake.variant_product_image(self.variant.id)
                       for _ in range(3)]

        self.categories = [fake.master_category(is_active=True) for _ in range(6)]
        self.providers = [fake.seller_prov() for _ in range(3)]
        self.policy = fake.shipping_policy(
            category_ids=[category.id for category in self.categories],
            provider_ids=[provider.id for provider in self.providers]
        )
        with logged_in_user(self.user):
            self.terminals = [fake.terminal(
                sellable_ids=[self.sellable.id],
                seller_id=current_user.seller_id
            )]

    def url(self):
        return '/sellable_products/%s/%s'

    def method(self):
        return 'GET'

    def assert_sellable_product_common_response(self, res):
        for k, v in self.sellable.__dict__.items():
            if isinstance(v, datetime.datetime):
                self.assertEqual(
                    v.strftime('%Y-%m-%d %H:%M:%S'),
                    res[camel_case(k)]
                )
            elif k == 'terminal_seo':
                self.assertEqual(
                    v.description,
                    res['detailedDescription']
                )
                self.assertEqual(
                    v.short_description,
                    res['description']
                )
            elif camel_case(k) in res and not isinstance(v, db.Model):
                self.assertEqual(
                    v,
                    res[camel_case(k)],
                )

    def assert_sellable_product_images_response(self, res):
        self.assertEqual(
            sorted(image.id for image in self.images),
            sorted(item['id'] for item in res)
        )

    def assert_sellable_product_specs_response(self, res):
        self.assertEqual(
            sorted(attribute.id for attribute in self.attributes),
            sorted(item['id'] for item in res)
        )

    def assert_sellable_product_terminals_response(self, res):
        # TODO: too hard to write tests :D will do later
        pass

    def test__passValidSellableProductIdWithTypeCommon__returnCorrectItem(self):
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (self.sellable.id, 'common')
            )

            self.assertEqual(200, code)
            self.assert_sellable_product_common_response(body['result']['common'])

    def test__passValidSellableProductIdWithTypeImages__returnCorrectItem(self):
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (self.sellable.id, 'images')
            )

            self.assertEqual(200, code)
            self.assert_sellable_product_images_response(body['result']['images'])

    def test__passValidSellableProductIdWithTypeSpecs__returnCorrectItem(self):
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (self.sellable.id, 'specs')
            )

            self.assertEqual(200, code)
            self.assert_sellable_product_specs_response(body['result']['specs'])

    def test__passValidSellableProductIdWithTypeTerminals__returnCorrectItem(self):
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (self.sellable.id, 'terminals')
            )

        self.assertEqual(200, code)
        self.assert_sellable_product_terminals_response(body['result']['terminals'])

    def test_passSellableProductIdNotExist__returnNotFoundException(self):
        with logged_in_user(self.user):
            code, _ = self.call_api(url=self.url() % (
                '123123213121321',
                random.choice(['common', 'images', 'specs', 'terminals'])
            ))

            self.assertEqual(404, code)

    def test_passInvalidDataKey__returnBadRequestException(self):
        with logged_in_user(self.user):
            code, _ = self.call_api(
                url=self.url() % (self.sellable.id, 'abcdef')
            )

            self.assertEqual(400, code)

    def test__shippingPropertyWithTypeCommonAndNotConfigMasterCategory__returnCorrectItem(self):
        sellable = fake.sellable_product(
            variant_id=self.variant.id,
            seller_id=1
        )

        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (sellable.id, 'common')
            )
            self.assertEqual(200, code)
            self.assertEqual(body['result']['common']['shippingProperty'], 'ALL')

    def test__shippingPropertyWithTypeCommonAndConfigRootMasterCategory__returnCorrectItem(self):
        sellable = fake.sellable_product(
            variant_id=self.variant.id,
            seller_id=1,
            provider_id=self.providers[0].id,
            master_category_id=self.categories[0].id
        )
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (sellable.id, 'common')
            )
            self.assertEqual(200, code)

            shipping_property = models.ShippingPolicy.query.join(
                models.ShippingPolicyMapping
            ).filter(
                models.ShippingPolicyMapping.category_id == self.categories[0].id,
                models.ShippingPolicyMapping.provider_id == self.providers[0].id
            ).first()

            self.assertEqual(body['result']['common']['shippingProperty'], shipping_property.shipping_type.upper())

    def test__shippingPropertyWithTypeCommonAndConfigLevel1MasterCategory__returnCorrectItem(self):
        """
        shippingProperty = nearest_level
        """
        parent_category = fake.master_category(is_active=True)
        l1_child_category = fake.master_category(is_active=True, parent_id=parent_category.id)
        l2_child_category = fake.master_category(is_active=True, parent_id=l1_child_category.id)
        fake.shipping_policy(
            category_ids=[category.id for category in [parent_category]],
            provider_ids=[provider.id for provider in self.providers],
            shipping_type='near'
        )
        fake.shipping_policy(
            category_ids=[category.id for category in [l1_child_category]],
            provider_ids=[provider.id for provider in self.providers],
            shipping_type='bulky'
        )
        sellable = fake.sellable_product(
            variant_id=self.variant.id,
            seller_id=1,
            provider_id=self.providers[0].id,
            master_category_id=l2_child_category.id
        )
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (sellable.id, 'common')
            )
            self.assertEqual(200, code)
            self.assertEqual(body['result']['common']['shippingProperty'], 'BULKY')

    def test__shippingPropertyWithTypeCommonAndConfigLevel2MasterCategory__returnCorrectItem(self):
        """
        shippingProperty = nearest_level
        """
        parent_category = fake.master_category(is_active=True)
        l1_child_category = fake.master_category(is_active=True, parent_id=parent_category.id)
        l2_child_category = fake.master_category(is_active=True, parent_id=l1_child_category.id)
        fake.shipping_policy(
            category_ids=[category.id for category in [parent_category]],
            provider_ids=[provider.id for provider in self.providers],
            shipping_type='near'
        )
        fake.shipping_policy(
            category_ids=[category.id for category in [l2_child_category]],
            provider_ids=[provider.id for provider in self.providers],
            shipping_type='bulky'
        )
        sellable = fake.sellable_product(
            variant_id=self.variant.id,
            seller_id=1,
            provider_id=self.providers[0].id,
            master_category_id=l2_child_category.id
        )
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (sellable.id, 'common')
            )
            self.assertEqual(200, code)
            self.assertEqual(body['result']['common']['shippingProperty'], 'BULKY')


class GetSellableProductItemsTestCase(APITestCase):
    ISSUE_KEY = 'SC-537'

    def setUp(self):
        self.variant = fake.product_variant()
        self.sellable = fake.sellable_product(variant_id=self.variant.id)
        self.user = fake.iam_user(seller_id=1)
        self.attributes = [fake.attribute(self.variant.id)
                           for _ in range(6)]

    def url(self):
        return '/sellable_products/%s/bundle/skus'

    def method(self):
        return 'GET'

    def test__passValidSellableProductId__returnBundleListSKUItems(self):
        with logged_in_user(self.user):
            fake.init_editing_status()
            fake.init_selling_status()

            children = [
                fake.sellable_product(
                    variant_id=self.variant.id,
                    editing_status_code='active',
                    seller_id=self.user.seller_id,
                    description=fake.text(),
                    detailed_description=fake.text(),
                    selling_status_code='hang_ban'
                ),
                fake.sellable_product(
                    variant_id=self.variant.id,
                    editing_status_code='processing',
                    seller_id=self.user.seller_id,
                    description=fake.text(),
                    detailed_description=fake.text(),
                    selling_status_code='hang_sap_het'
                )
            ]
            fake.bundle(self.sellable, children)

            bundles = SellableProductBundle.query.filter(
                SellableProductBundle.bundle_id == self.sellable.id
            ).all()

            code, body = self.call_api(
                url=self.url() % (self.sellable.id)
            )

            self.assertEqual(code, 200)

            result = body['result']['items']
            self.assertEqual(len(result), 2)

            for i in range(len(result)):
                self.assertEqual(result[i].get('id'), children[i].id)
                self.assertEqual(result[i].get('sku'), children[i].sku)
                self.assertEqual(result[i].get('name'), children[i].name)
                self.assertEqual(result[i].get('sellingStatus').get('code'), children[i].selling_status_code)
                self.assertIsNotNone(result[i].get('sellingStatus').get('name'))
                self.assertIsNotNone(result[i].get('sellingStatus').get('config'))
                self.assertEqual(result[i].get('allowSellingWithoutStock'),
                                 bool(children[i].allow_selling_without_stock))
                self.assertEqual(result[i].get('name'), children[i].name)
                self.assertEqual(result[i].get('editingStatus').get('code'), children[i].editing_status_code)
                self.assertIsNotNone(result[i].get('editingStatus').get('name'))
                self.assertIsNotNone(result[i].get('editingStatus').get('config'))
                self.assertEqual(result[i].get('quantity'), bundles[i].quantity)
                self.assertEqual(result[i].get('priority'), bundles[i].priority)

    def test__passValidSellableProductId__returnBundleEmptyList(self):
        with logged_in_user(self.user):
            self.sellable.is_bundle = True

            code, body = self.call_api(
                url=self.url() % (self.sellable.id)
            )

            self.assertEqual(code, 200)
            self.assertEqual(len(body['result']['items']), 0)

    def test__passNotBundleSellableProductId__returnBundleEmptyList(self):
        with logged_in_user(self.user):
            self.sellable.is_bundle = False

            code, body = self.call_api(
                url=self.url() % (self.sellable.id)
            )

            self.assertEqual(code, 400)
            self.assertEqual(body['code'], 'INVALID')
            self.assertEqual(body['message'], 'Sản phẩm không phải là 1 bundle')

    def test__passNotExistSellableProductId__returnBundleEmptyList(self):
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.url() % (123)
            )

            self.assertEqual(code, 400)
            self.assertEqual(body['code'], 'INVALID')
            self.assertEqual(body['message'], 'Sản phẩm không tồn tại')

    def test__whenOneOfThreeSellableProductNotExist_returnThreeSkusInList(self):
        with logged_in_user(self.user):
            fake.init_editing_status()
            sellable_product = fake.sellable_product(
                variant_id=self.variant.id,
                editing_status_code='active',
                seller_id=self.user.seller_id,
                description=fake.text(),
                detailed_description=fake.text(),
            )
            children = [sellable_product]
            sellable_product_2 = deepcopy(sellable_product)
            sellable_product_2.id = 100
            children.append(sellable_product_2)

            fake.bundle(self.sellable, children)

            bundles = SellableProductBundle.query.filter(
                SellableProductBundle.bundle_id == self.sellable.id
            ).all()

            code, body = self.call_api(
                url=self.url() % (self.sellable.id)
            )

            self.assertEqual(code, 200)

            result = body['result']['items']
            self.assertEqual(len(result), 1)

            self.assertEqual(result[0].get('id'), children[0].id)
            self.assertEqual(result[0].get('sku'), children[0].sku)
            self.assertEqual(result[0].get('name'), children[0].name)
            self.assertEqual(result[0].get('editingStatus').get('code'), children[0].editing_status_code)
            self.assertIsNotNone(result[0].get('editingStatus').get('name'))
            self.assertIsNotNone(result[0].get('editingStatus').get('config'))
            self.assertEqual(result[0].get('quantity'), bundles[0].quantity)
            self.assertEqual(result[0].get('priority'), bundles[0].priority)


class GetSellableProductShippingTypesTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-439'
    FOLDER = '/Sellable/Get'

    def setUp(self):
        self.products = [fake.product() for _ in range(3)]
        self.variants = [fake.product_variant(
            product_id=random.choice([product.id for product in self.products])
        ) for _ in range(3)]
        self.sellable_product_multiple_shipping_types = fake.sellable_product(
            sku=f'123456789121',
            variant_id=random.choice([variant.id for variant in self.variants]),
            seller_id=1
        )
        self.sellable_product_only_one_shipping_type = fake.sellable_product(
            sku=f'123456789122',
            variant_id=random.choice([variant.id for variant in self.variants]),
            seller_id=1
        )
        self.sellable_product_no_shipping_type = fake.sellable_product(
            sku=f'123456789123',
            variant_id=random.choice([variant.id for variant in self.variants]),
            seller_id=1
        )

        self.shipping_types = [fake.shipping_type() for _ in range(3)]
        sellable_product_ids = [self.sellable_product_multiple_shipping_types.id,
                                self.sellable_product_multiple_shipping_types.id,
                                self.sellable_product_only_one_shipping_type.id]
        self.sku_shipping_types = [fake.sellable_product_shipping_type(
            sellable_product_id=sellable_product_ids[i],
            shipping_type_id=self.shipping_types[i].id
        ) for i in range(3)]
        self.user = fake.iam_user(seller_id=1)

    def url(self):
        return '/sellable_products/sku/%s/common'

    def method(self):
        return 'GET'

    def __init_query(self, sku):
        code, body = self.call_api_with_login(
            url=self.url() % (sku)
        )
        common = body['result']['common']
        return code, common

    def test__200__returnNoShippingType(self):
        code, common = self.__init_query(self.sellable_product_no_shipping_type.sku)

        self.assertEqual(code, 200)
        self.assertEqual(len(common['shippingTypes']), 0)

    def test__200__returnOnlyOneShippingType(self):
        expect_shipping_type = self.shipping_types[2]

        code, common = self.__init_query(self.sellable_product_only_one_shipping_type.sku)

        self.assertEqual(code, 200)
        self.assertEqual(len(common['shippingTypes']), 1)
        self.assertEqual(common['shippingTypes'][0]['id'], expect_shipping_type.id)
        self.assertEqual(common['shippingTypes'][0]['code'], expect_shipping_type.code)
        self.assertEqual(common['shippingTypes'][0]['name'], expect_shipping_type.name)

    def test__200__returnMultipleShippingTypes(self):
        code, common = self.__init_query(self.sellable_product_multiple_shipping_types.sku)

        self.assertEqual(code, 200)
        self.assertEqual(len(common['shippingTypes']), 2)
        actual_results = sorted(common['shippingTypes'], key=lambda i: i['id'])

        for i in range(2):
            self.assertEqual(actual_results[i]['id'], self.shipping_types[i].id)
            self.assertEqual(actual_results[i]['code'], self.shipping_types[i].code)
            self.assertEqual(actual_results[i]['name'], self.shipping_types[i].name)
