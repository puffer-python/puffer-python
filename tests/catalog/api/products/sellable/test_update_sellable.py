# coding=utf-8

from mock import patch

from tests.catalog.api import APITestCase
from catalog import models
from tests.faker import fake
from tests import logged_in_user


class SetupUpdateSellableProduct(APITestCase):
    def url(self):
        return f'/sellable_products/{self.sellable.id}'

    def method(self):
        return 'PATCH'

    def setUp(self):
        self.user = fake.iam_user()
        product = fake.product()
        variant = fake.product_variant(product_id=product.id)
        self.sellable = fake.sellable_product(
            variant_id=variant.id,
            editing_status_code='active',
            seller_id=self.user.seller_id
        )
        self.data = {}
        fake.init_editing_status()

        self.shipping_type = fake.shipping_type()

        fake.sellable_product_shipping_type(
            self.sellable.id,
            self.shipping_type.id
        )


class UpdateSellableProductTestCase(SetupUpdateSellableProduct):
    # ISSUE_KEY = 'SC-480'
    ISSUE_KEY = 'SC-655'

    def test_passSellableName__returnSellableProduct(self):
        self.data['name'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 200, body
        assert body['result']['name'] == self.data['name']

    def test_updateSellable__whenSellableActived(self):
        self.sellable.editing_status_code = 'active'
        models.db.session.commit()
        self.data['name'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 200, body
        assert body['result']['name'] == self.data['name']

    def test_updateSellable__whenSellablePendingApproval(self):
        self.sellable.editing_status_code = 'pending_approval'
        models.db.session.commit()
        self.data['name'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 200, body
        assert body['result']['name'] == self.data['name']

    def test_updateSellable__whenSellableInject(self):
        self.sellable.editing_status_code = 'reject'
        models.db.session.commit()
        self.data['name'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 200, body
        assert body['result']['name'] == self.data['name']
        assert 'editingStatusCode' in body['result']

    def test_passNameExisted__raiseBadRequestException(self):
        other_sellable = fake.sellable_product(
            variant_id=self.sellable.variant_id,
            editing_status_code='active',
            seller_id=self.user.seller_id
        )
        self.data['name'] = other_sellable.name
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 200, body

    def test_passCategoryNotExist__raiseBadRequestException(self):
        self.data['categoryId'] = fake.random_int(100, 1000)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passCategoryInactive__raiseBadRequestException(self):
        cat = fake.category(is_active=False)
        self.data['categoryId'] = cat.id
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passBrandNotExist__raiseBadRequestException(self):
        self.data['brandId'] = fake.random_int(100, 1000)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passBrandInactive__raiseBadRequestException(self):
        brand = fake.brand(is_active=False)
        self.data['brandId'] = brand.id
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passTaxCodeInvalid__raiseBadRequestException(self):
        self.data['taxInCode'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

        self.data.pop('taxInCode')
        self.data['taxOutCode'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passManageSerialInvalid__raiseBadRequestException(self):
        self.data['manageSerial'] = False
        self.data['autoGenerateSerial'] = True
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passUnitIdNotExist__raiseBadRequestException(self):
        self.data['unitId'] = fake.random_int(100, 1000)
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_passTypeInvalid__raiseBadRequestException(self):
        self.data['type'] = fake.text()
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_updateExpiryTrackingToFalse__raiseBadRequestException(self):
        self.sellable.expiry_tracking = True
        self.data['expiryTracking'] = False
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_updateExpirationTypeInvalid__raiseBadRequestException(self):
        self.sellable.expiry_tracking = True
        self.data['expirationType'] = 69
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_setExpirationTypeToNull__raiseBadRequestException(self):
        self.sellable.expiry_tracking = True
        self.data['expirationType'] = None
        with logged_in_user(self.user):
            code, body = self.call_api(self.data)
        assert code == 400, body

    def test_updateProviderInvalid__raiseBadRequestException(self):
        with patch('catalog.services.provider.get_provider_by_id') as mock_get_provider:
            mock_get_provider.return_value = {
                'id': 2,
                'sellerID': 2,
                'isActive': 1
            }
            self.data['providerId'] = 2
            with logged_in_user(self.user):
                code, body = self.call_api(self.data)
            assert code == 400
            assert body['message'] == 'Nhà cung cấp không hợp lệ'

    def test_200_validShippingTypes(self):
        shipping_types = [fake.shipping_type() for _ in range(2)]
        self.data['shippingTypes'] = [x.id for x in shipping_types]
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

            sellable_shipping_types = models.SellableProductShippingType.query.all()
            self.assertEqual(len(sellable_shipping_types), 2)
            for sellable_shipping_type in sellable_shipping_types:
                self.assertIn(sellable_shipping_type.shipping_type_id, self.data['shippingTypes'])

    def test_200_deleteCurrentShippingTypeWhenInputtingAnEmptyList(self):
        self.data['shippingTypes'] = []
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

            sellable_shipping_types = models.SellableProductShippingType.query.all()
            self.assertEqual(len(sellable_shipping_types), 0)

    def test_400_notExistShippingTypes(self):
        self.data['shippingTypes'] = [123]
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

            sellable_shipping_types = models.SellableProductShippingType.query.all()
            self.assertEqual(len(sellable_shipping_types), 1)
            self.assertEqual(sellable_shipping_types[0].shipping_type_id, self.shipping_type.id)

    def test_400_inactiveShippingTypes(self):
        shipping_types = [fake.shipping_type(), fake.shipping_type(is_active=0)]
        self.data['shippingTypes'] = [x.id for x in shipping_types]

        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)
            self.assertEqual(body['message'], 'Shipping type không tồn tại hoặc đã bị vô hiệu')

            sellable_shipping_types = models.SellableProductShippingType.query.all()
            self.assertEqual(len(sellable_shipping_types), 1)
            self.assertEqual(sellable_shipping_types[0].shipping_type_id, self.shipping_type.id)

    def test_200_ShippingTypesFieldIsNull(self):
        self.data['shippingTypes'] = None
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

            sellable_shipping_types = models.SellableProductShippingType.query.all()
            self.assertEqual(len(sellable_shipping_types), 1)
            self.assertEqual(sellable_shipping_types[0].shipping_type_id, self.shipping_type.id)


class TestAllowMasterCategoryNone(SetupUpdateSellableProduct):
    ISSUE_KEY = 'CATALOGUE-251'
    FOLDER = '/Sellable/Update'

    @patch('catalog.services.products.sellable.signals.sellable_common_update_signal.send', return_value=None)
    def test_updateSellableProduct_passExistMasterCategoryId_200_updateSuccessfully(self, mock):
        self.data['masterCategoryId'] = fake.master_category(is_active=True).id
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

        sellable = models.SellableProduct.query.get(self.sellable.id)
        self.assertEqual(sellable.master_category.id, self.data['masterCategoryId'])
        mock.assert_called_once()

    @patch('catalog.services.products.sellable.signals.sellable_common_update_signal.send', return_value=None)
    def test_updateSellableProduct_passNoneMasterCategoryId_200_updateSuccessfully(self, mock):
        self.data['masterCategoryId'] = None
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code)

        sellable = models.SellableProduct.query.get(self.sellable.id)
        self.assertIsNone(sellable.master_category)
        mock.assert_called_once()

    def test_updateSellableProduct_notPassMasterCategoryId_200_updateSuccessfully(self):
        # test_passSellableName__returnSellableProduct
        pass

    def test_updateSellableProduct_400_masterCategoryNotExist(self):
        self.data['masterCategoryId'] = 123
        with logged_in_user(self.user):
            code, body = self.call_api(data=self.data)
            self.assertEqual(400, code)


class UpdateSellableProductWithDefaultShippingTypeTestCase(SetupUpdateSellableProduct):
    ISSUE_KEY = 'CATALOGUE-703'
    FOLDER = '/Sellable/UpdateSellableProductWithDefaultShippingTypeTestCase'

    def assert_default_shipping_type(self):
        sellable_shipping_types = models.SellableProductShippingType.query.filter(
            models.SellableProductShippingType.sellable_product_id == self.sellable.id
        ).all()
        self.assertEqual(len(sellable_shipping_types), 1)
        sellable_shipping_type = sellable_shipping_types[0]
        self.assertEqual(sellable_shipping_type.shipping_type_id, self.shipping_type_default.id)

    def test_200_update_without_shipping_type_in_param(self):
        product = fake.product()
        variant = fake.product_variant(product_id=product.id)
        self.sellable = fake.sellable_product(
            variant_id=variant.id,
            editing_status_code='active',
            seller_id=self.user.seller_id
        )
        self.shipping_type_default = fake.shipping_type(is_default=1)
        with logged_in_user(self.user):
            self.data['name'] = fake.text()
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code, body)

            self.assert_default_shipping_type()

    def test_200_update_with_shipping_type_is_empty_in_param(self):
        self.shipping_type_default = fake.shipping_type(is_default=1)
        with logged_in_user(self.user):
            self.data['shippingTypes'] = []
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code, body)

            self.assert_default_shipping_type()


class TestUpdateModelSellableProduct(SetupUpdateSellableProduct):
    ISSUE_KEY = 'CATALOGUE-1221'
    FOLDER = '/Sellable/UpdateModel'

    def test_200_update_within_model_in_param(self):
        product = fake.product()
        variant = fake.product_variant(product_id=product.id)
        self.sellable = fake.sellable_product(
            variant_id=variant.id,
            editing_status_code='active',
            seller_id=self.user.seller_id
        )
        self.shipping_type_default = fake.shipping_type(is_default=1)
        with logged_in_user(self.user):
            model = fake.text()
            self.data['model'] = model
            code, body = self.call_api(data=self.data)

            self.assertEqual(200, code, body)
            self.assertEqual(product.model, model)
            sellable_products = models.SellableProduct.query.filter(
                models.SellableProduct.product_id == product.id
            ).all()
            for sellable_product in sellable_products:
                self.assertEqual(sellable_product.model, model)

    def test_200_update_without_model_in_param(self):
        product = fake.product()
        variant = fake.product_variant(product_id=product.id)
        self.sellable = fake.sellable_product(
            variant_id=variant.id,
            editing_status_code='active',
            seller_id=self.user.seller_id
        )
        self.shipping_type_default = fake.shipping_type(is_default=1)
        with logged_in_user(self.user):
            self.data['name'] = fake.text()
            code, body = self.call_api(data=self.data)
            self.assertEqual(200, code, body)
