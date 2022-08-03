# coding=utf-8
from unittest.mock import patch

from flask import current_app

from catalog import constants, models
import json
import random

from tests.catalog.api import APITestCase
from tests.faker import fake


class TestCreateListSKuLayerSKU(APITestCase):
    ISSUE_KEY = 'CATALOGUE-967'
    FOLDER = '/Sku/CreateListSku/SkuLayer'

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

    def setUp(self):
        fake.init_editing_status()
        self.created_by = 'dungbv'
        self.seller = fake.seller()
        self.category = fake.category(is_active=True)
        self.master_category = fake.master_category(is_active=True)
        self.brand = fake.brand()
        self.tax = fake.tax(code="10")
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def _init_attribute_set(self, is_variation=1):
        self.attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(
            set_id=self.attribute_set.id,
            system_group=False
        )
        self.attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 3)
        ]

        self.attribute_options = [
            fake.attribute_option(self.attributes[0].id, value='Vàng'),
            fake.attribute_option(self.attributes[0].id, value='Đỏ'),
            fake.attribute_option(self.attributes[1].id, value='S'),
            fake.attribute_option(self.attributes[1].id, value='XXL'),
        ]

        fake.attribute_group_attribute(
            attribute_id=self.attributes[0].id,
            group_ids=[attribute_group.id],
            is_variation=is_variation
        )
        fake.attribute_group_attribute(
            attribute_id=self.attributes[1].id,
            group_ids=[attribute_group.id],
            is_variation=is_variation
        )

    def _init_uom(self):
        self.uom_attribute_group = fake.attribute_group(
            set_id=self.attribute_set.id,
            system_group=True
        )
        self.uom_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[self.uom_attribute_group.id],
            is_variation=1
        )
        self.uom_ratio_attribute = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[self.uom_attribute_group.id],
            is_variation=1
        )
        self.uom_attr_options = [
            fake.attribute_option(self.uom_attribute.id, value='Cái'),
            fake.attribute_option(self.uom_attribute.id, value='Chiếc')
        ]
        self.ratio_attr_options = [
            fake.attribute_option(self.uom_ratio_attribute.id, value='1'),
            fake.attribute_option(self.uom_ratio_attribute.id, value='2')
        ]

    def _init_products(self, update=True):
        if update:
            self.product = fake.product(
                category_id=self.category.id,
                master_category_id=self.master_category.id,
                created_by=self.created_by,
                attribute_set_id=self.attribute_set.id)

            self.product_category = fake.product_category(
                product_id=self.product.id,
                category_id=self.category.id
            )
            self.payload = {
                'productId': self.product.id,
            }
        else:
            self.payload = {
                'taxInCode': self.tax.code,
                'productName': fake.text(),
                'categoryId': self.category.id,
                'brandId': self.brand.id,
                'providerId': 2,
                'masterCategoryId': self.master_category.id,
                'model': fake.text(),
                'warrantyMonths': fake.integer(max=12)
            }
        self.payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'attributeSetId': self.attribute_set.id,
            **self.payload
        }

    def _init_variants(self, is_variation=False, count=1, update=True):
        self.payload_variants = []
        for index in range(count):
            variant = {}
            if not update:
                if not is_variation:
                    variant = {
                        'uomId': self.uom_attr_options[index].id,
                        'uomRatio': self.ratio_attr_options[index].value,
                        'attributes': [{
                            'id': self.attributes[0].id,
                            'value': str(self.attribute_options[index].id)
                        }, {
                            'id': self.attributes[1].id,
                            'value': str(self.attribute_options[index + 2].id)
                        }]
                    }
                    self.payload_variants.append(variant)
                else:
                    for index_2 in range(len(self.uom_attr_options)):
                        variant_2 = {
                            'uomId': self.uom_attr_options[index_2].id,
                            'uomRatio': self.ratio_attr_options[index_2].value,
                            'attributes': [{
                                'id': self.attributes[0].id,
                                'value': str(self.attribute_options[index].id)
                            }, {
                                'id': self.attributes[1].id,
                                'value': str(self.attribute_options[index + 2].id)
                            }]
                        }
                        self.payload_variants.append(variant_2)
            else:
                product_variant = fake.product_variant(
                    product_id=self.product.id,
                    uom_option_value=self.uom_attr_options[index].id,
                    uom_ratio_value=self.ratio_attr_options[index].value
                )
                variant['variantId'] = product_variant.id
                self.payload_variants.append(variant)

    def _init_skus(self, update=True, **kwargs):
        for variant in self.payload_variants:
            if not update:
                variant['sku'] = {
                    'images': [],
                    'trackingType': False,
                    'expiryTracking': False,
                    'daysBeforeExpLock': fake.integer(),
                    'productType': random.choice(['product', 'consu']),
                    'sellerSku': kwargs.get('seller_sku') or fake.text()
                }
            else:
                sku = fake.sellable_product(variant_id=variant['variantId'], seller_id=self.category.seller_id,
                                            **kwargs)
                fake.product_variant_images(variant_id=sku.variant_id)
                variant['sku'] = {
                    'sku': sku.sku
                }

    def _init_payload(self,
                       count=2, is_variation=False,
                       update_product=True, update_variant=True, update_sku=False, **kwargs):
        self.payload = {}
        self._init_attribute_set(is_variation)
        self._init_uom()
        self.category = fake.category(is_active=True, attribute_set_id=self.attribute_set.id, seller_id=self.seller.id)
        self._init_products(update=update_product)
        self._init_variants(is_variation=is_variation, update=update_variant, count=count)
        self._init_skus(update=update_sku, **kwargs)

        self.payload = {
            **self.payload,
            'variants': self.payload_variants
        }
        return self.payload

class TestCreateListSKuLayerSKUCommon(TestCreateListSKuLayerSKU):
    ISSUE_KEY = 'CATALOGUE-967'
    FOLDER = '/Sku/CreateListSku/SkuLayer'

    def testCreateListSKu_test_with_only_required_field_return200_success_create(self):
        self._init_payload()
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)

    def testCreateListSKu_test_with_sku_param_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['sku'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testUpdateListSKu_test_invalid_sku_param_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['name'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_name_param_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['name'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))
        sku_has_name = models.SellableProduct.query.filter_by(
            seller_sku=self.payload['variants'][0]['sku']['sellerSku']
        ).first()
        self.assertEqual(self.payload['variants'][0]['sku']['name'], sku_has_name.name)
        sku_has_default_name = models.SellableProduct.query.all()
        for sku in sku_has_default_name:
            self.assertIsNotNone(sku.name)

    def testCreateListSKu_test_check_generate_name_param_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['name'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)

    def testCreateListSKu_test_with_name_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['name'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_name_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['name'] = fake.text(255 + fake.integer())
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_seller_sku_length_over_20_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['sellerSku'] = fake.text(20 + fake.integer())
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_seller_sku_length_20_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['sellerSku'] = fake.text(20)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateSKu_testMissingSellerSku(self):
        self._init_payload()
        del self.payload['variants'][0]['sku']['sellerSku']
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)
        self.assertEqual(body['message'], 'Vui lòng bổ sung Mã sản phẩm')

    def testCreateListSKu_test_with_not_barcode_return200_success_create(self):
        self._init_payload()
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_barcode_exist_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['barcode'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_barcode_duplicate_variant_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['barcode'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_not_partNumber_return200_success_create(self):
        self._init_payload()
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_partNumber_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['partNumber'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_partNumber_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['partNumber'] = fake.text(255 + 1)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_trackingType_not_boolean_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['trackingType'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_expiryTracking_not_boolean_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['expiryTracking'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_expirationType_not_integer_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['expirationType'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_daysBeforeExpLock_not_integer_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['expirationType'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_productType_not_enum_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['productType'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_shippingTypeId_return200_success_create(self):
        self._init_payload()
        shipping_type = fake.shipping_type()
        default_shipping_type = fake.shipping_type(is_default=1)
        self.payload['variants'][0]['sku']['shippingTypeId'] = shipping_type.id
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))
        sku_shipping_type = models.SellableProduct.query.filter_by(
            seller_sku=self.payload['variants'][0]['sku']['sellerSku']
        ).first()
        self.assertEqual(shipping_type.id, sku_shipping_type.shipping_type_id)
        sku_default_shipping_types = models.SellableProduct.query.filter(
            models.SellableProduct.seller_sku.notin_([self.payload['variants'][0]['sku']['sellerSku']])
        ).all()
        for sku in sku_default_shipping_types:
            self.assertEqual(sku.shipping_type_id, default_shipping_type.id)

    def testCreateListSKu_test_with_shippingTypeId_without_system_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['shippingTypeId'] = [fake.integer()]
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_displayName_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['displayName'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_displayName_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['displayName'] = fake.text(255 + 1)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_metaTitle_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['metaTitle'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_metaTitle_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['metaTitle'] = fake.text(255 + 1)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_metaDescription_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['metaDescription'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_metaDescription_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['metaDescription'] = fake.text(255 + 1)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_metaKeyword_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['metaKeyword'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_metaKeyword_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['metaDescription'] = fake.text(255 + 1)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_urlKey_length_255_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['urlKey'] = fake.text(255)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_urlKey_length_over_255_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['urlKey'] = fake.text(255 + 1)
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_description_length_500_return200_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['description'] = fake.text(500)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, json.dumps(self.payload))

    def testCreateListSKu_test_with_description_length_over_500_return400_success_create(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['description'] = fake.text(500 + fake.integer())
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, json.dumps(self.payload))

    def testCreateListSKu_test_withEditingStatusCode_withoutSku_return200(self):
        self._init_payload(count=1)
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'active'
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        seller_sku = self.payload['variants'][0]['sku']['sellerSku']
        sku = models.SellableProduct.query.filter_by(
            seller_sku=seller_sku
        ).first()
        self.assertEqual(sku.editing_status_code, 'processing')

    def testCreateListSKu_test_withoutEditingStatusCode_withoutSku_return200_autoSetEditingStatus(self):
        self._init_payload(count=1)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        seller_sku = self.payload['variants'][0]['sku']['sellerSku']
        sku = models.SellableProduct.query.filter_by(
            seller_sku=seller_sku
        ).first()
        self.assertEqual(sku.editing_status_code, 'processing')

    @patch('catalog.validators.sellable.SellableProductValidator.validate_provider_id')
    @patch('catalog.api.product.sku.sku._upsert_variant_images')
    def testCreateListSKu_test_withEditingStatusCode_withSku_return200_updateEditingStatus(
            self, mock_image, mock_provider_id):
        mock_image.return_value = None
        self._init_payload(count=1, update_sku=True, editing_status_code='processing')
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'pending_approval'
        sku = self.payload['variants'][0]['sku']['sku']
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        sku = models.SellableProduct.query.filter_by(
            sku=sku
        ).first()
        self.assertEqual(sku.editing_status_code, 'pending_approval')

    @patch('catalog.api.product.sku.sku._upsert_variant_images')
    def testCreateListSKu_test_withInvalidEditingStatusCode_withSku_return400(self, mock_image):
        mock_image.return_value = None
        self._init_payload(count=1, update_sku=True, editing_status_code='processing')
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'dfdsfsdfsd'
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)

    def testCreateListSKu_test_withEditingStatusCode_withSku_return200_keepCurrentStatus(self):
        self._init_payload(count=1, update_sku=True, editing_status_code='processing')
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'processing'
        sku = self.payload['variants'][0]['sku']['sku']
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        sku = models.SellableProduct.query.filter_by(
            sku=sku
        ).first()
        self.assertEqual(sku.editing_status_code, 'processing')

    @patch('catalog.api.product.sku.sku._upsert_variant_images')
    def testCreateListSKu_test_withEditingStatusCode_withSku_return400_canNotMoveFromProcessingToActive(self,
                                                                                                        mock_image):
        mock_image.return_value = None
        self._init_payload(count=1, update_sku=True, editing_status_code='processing')
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'active'
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)

    @patch('catalog.api.product.sku.sku._upsert_variant_images')
    def testCreateListSKu_test_withEditingStatusCode_withSku_return400_canNotMoveFromActiveToProcessing(self,
                                                                                                        mock_image):
        mock_image.return_value = None
        self._init_payload(count=1, update_sku=True, editing_status_code='active')
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'processing'
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)

    @patch('catalog.api.product.sku.sku._upsert_variant_images')
    def testCreateListSKu_test_withEditingStatusCode_withSku_return400_canNotMoveFromInactiveToProcessing(self,
                                                                                                          mock_image):
        mock_image.return_value = None
        self._init_payload(count=1, update_sku=True, editing_status_code='inactive')
        self.payload['variants'][0]['sku']['editingStatusCode'] = 'processing'
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code)

    def testCreateListSKu_test_withProviderId_withoutProductId_return200_createForAllSku(self):
        self._init_payload(count=1, update_product=False, update_variant=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        skus = models.SellableProduct.query.all()
        for sku in skus:
            self.assertEqual(sku.provider_id, 2)
        product = models.Product.query.get(body['result'].get('productId'))
        self.assertEqual(product.provider_id, 2)

    def testCreateListSKu_test_withProviderId_withProductId_return200_updateForAllSku(self):
        self._init_payload(count=2, update_sku=True, provider_id=3)
        self.payload['providerId'] = 2
        self.payload['variants'] = self.payload['variants'][:1]  # remove the 3rd variants
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        skus = models.SellableProduct.query.all()
        for sku in skus:
            self.assertEqual(sku.provider_id, 2)
        product = models.Product.query.get(self.payload.get('productId'))
        self.assertEqual(product.provider_id, 2)

    def testCreateListSKu_test_createNew_withoutImage_return200(self):
        self._init_payload(count=1, update_product=False, update_variant=False, update_sku=False)
        del self.payload['variants'][0]['sku']['images']
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)

    def testCreateListSKu_test_return200_with_new_variants(self):
        self.product = fake.product(
            category_id=self.category.id,
            master_category_id=self.master_category.id,
            created_by=self.created_by)

        self.product_category = fake.product_category(
            product_id=self.product.id,
            category_id=self.category.id
        )

        group = fake.attribute_group(self.product.attribute_set_id)
        attribute_uom = fake.attribute(code=constants.UOM_CODE_ATTRIBUTE)
        attribute_ratio = fake.attribute(code=constants.UOM_RATIO_CODE_ATTRIBUTE)
        variant_attributes = [fake.attribute(value_type='selection') for _ in range(5)]
        for a in variant_attributes:
            fake.attribute_option(a.id)
        uom_options = [fake.attribute_option(attribute_uom.id) for _ in range(2)]
        uom_attributes = [attribute_uom, attribute_ratio]
        attribute_group_attribute = [fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[group.id],
            is_variation=True
        ) for attr in variant_attributes]
        for attr in uom_attributes:
            fake.attribute_group_attribute(
                attribute_id=attr.id,
                group_ids=[group.id],
                is_variation=True
            )
        models.db.session.commit()
        variants = []
        for i in range(2):
            attributes = []
            for attr in attribute_group_attribute:
                attributes.append({
                    'id': attr.attribute_id,
                    'value': str(fake.random_element(attr.attribute.options).id)
                })
            variants.append({
                'uomId': uom_options[i].id,
                'uomRatio': 1.0,
                'attributes': attributes,
                'sku': {
                    'images': [],
                    'trackingType': False,
                    'expiryTracking': True,
                    'expirationType': 2,
                    'daysBeforeExpLock': fake.integer(),
                    'productType': random.choice(['product', 'consu']),
                    'sellerSku': fake.text()
                }
            })
        payload = {
            'createdBy': self.created_by,
            'sellerId': self.category.seller_id,
            'productId': self.product.id,
            'attributeSetId': self.product.attribute_set_id,
            'variants': variants
        }
        code, body = self.call_api(payload)
        self.assertEqual(200, code, json.dumps(payload))

    def test_updateSku_with_sku_not_exist(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['sku'] = fake.text()
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, body)
        self.assertEqual(body.get('message'), 'Không tồn tại sản phẩm')

    def _init_sku(self):
        self._init_payload()
        code, body = self.call_api(self.payload)
        return body.get('result').get('variants')

    def test_updateSku_success(self):
        init_skus = self._init_sku()
        random_sku = random.choice(self.payload.get('variants'))
        for init_sku in init_skus:
            if random_sku.get('variantId') == init_sku.get('variantId'):
                random_sku['sku']['sku'] = init_sku.get('sku')
        self.payload['variants'] = [random_sku]
        self.assertIsNotNone(random_sku.get('sku').get('sku'), random_sku)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        self.assertEqual(len(body['result']['variants']), len(self.payload['variants']))
        self.assertEqual(body['result']['variants'][0]['sku'], self.payload['variants'][0]['sku']['sku'])

    def testCreateListSKu_test_createSku_WithTrackingType_return200(self):
        self._init_payload()
        self.payload['variants'][0]['sku']['trackingType'] = True
        code, body = self.call_api(self.payload)
        sku_id = body['result']['variants'][0]['skuId']
        sellable = models.SellableProduct.query.get(sku_id)
        self.assertEqual(sellable.tracking_type, True)

    def testCreateListSKu_test_updateSku_WithTrackingType_return200(self):
        self._init_payload(count=1, update_sku=True, tracking_type=False)
        self.payload['variants'][0]['sku']['trackingType'] = True
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200, body)
        sku_id = body['result']['variants'][0]['skuId']
        sellable = models.SellableProduct.query.get(sku_id)
        self.assertEqual(sellable.tracking_type, True)

    def test_return200_updateOldVariant_andCreateNewVariantAttribute(self):
        self._init_payload(is_variation=1, count=1, update_variant=False, update_sku=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200)
        for i in range(len(self.payload['variants'])):
            del self.payload['variants'][i]['uomId']
            del self.payload['variants'][i]['attributes']
            del self.payload['variants'][i]['uomRatio']
            self.payload['variants'][i]['variantId'] = body['result']['variants'][i]['variantId']
            self.payload['variants'][i]['sku']['sku'] = body['result']['variants'][i]['sku']

        for i in range(len(self.uom_attr_options)):
            variant = {
                'uomId': self.uom_attr_options[i].id,
                'uomRatio': self.ratio_attr_options[i].value,
                'attributes': [{
                    'id': self.attributes[0].id,
                    'value': str(self.attribute_options[1].id)
                }, {
                    'id': self.attributes[1].id,
                    'value': str(self.attribute_options[2].id)
                }],
                'sku': {
                    'images': [],
                    'trackingType': False,
                    'expiryTracking': True,
                    'expirationType': random.choice([1, 2]),
                    'daysBeforeExpLock': fake.integer(),
                    'productType': random.choice(['product', 'consu']),
                    'sellerSku': fake.text()
                }
            }
            self.payload['variants'].append(variant)
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200, body)

    def test_return200_updateOldVariant(self):
        self._init_payload(is_variation=1, count=1, update_variant=False, update_sku=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200)
        for i in range(len(self.payload['variants'])):
            del self.payload['variants'][i]['uomId']
            del self.payload['variants'][i]['attributes']
            del self.payload['variants'][i]['uomRatio']
            self.payload['variants'][i]['variantId'] = body['result']['variants'][i]['variantId']
            self.payload['variants'][i]['sku']['sku'] = body['result']['variants'][i]['sku']
            self.payload['variants'][i]['sku']['name'] = 'Hello'
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200, body)

    def test_return200_withExpiryTracking_withSku(self):
        self._init_payload(
            count=1, update_sku=True,
            expiry_tracking=True, expiration_type=2, days_before_exp_lock=3, is_bundle=False)
        self.payload['variants'][0]['sku']['expiryTracking'] = True
        self.payload['variants'][0]['sku']['expirationType'] = 2
        self.payload['variants'][0]['sku']['daysBeforeExpLock'] = 3
        sku = self.payload['variants'][0]['sku']['sku']
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        sku = models.SellableProduct.query.filter_by(
            sku=sku
        ).first()
        self.assertEqual(sku.expiry_tracking, True)
        self.assertEqual(sku.expiration_type, 2)

    def test_create2Skus_withDifferentUrlKey_return200(self):
        self._init_payload(count=2, update_variant=False, update_sku=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code)
        sku_seos = models.SellableProductSeoInfoTerminal.query.all()
        self.assertEqual(len(sku_seos), 2)
        self.assertNotEqual(sku_seos[0].static_url_key, sku_seos[1].static_url_key)

    def test_createProduct_withAllAutoGenerateVariantNameCases(self):
        self._init_payload(is_variation=1, count=2, update_variant=False, update_sku=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200)
        product = models.Product.query.get(body['result'].get('productId'))
        variants = models.ProductVariant.query.all()
        self.assertEqual(variants[0].name, f'{product.name} (Vàng, S)')
        self.assertEqual(variants[1].name, f'Chiếc 2.0 Cái {product.name} (Vàng, S)')
        self.assertEqual(variants[2].name, f'{product.name} (Đỏ, XXL)')
        self.assertEqual(variants[3].name, f'Chiếc 2.0 Cái {product.name} (Đỏ, XXL)')

    def test_withProductFields_withoutProductId_return200_createForAllSku(self):
        """
        ProductFields:
        category, master_category,
        provider_id, wanrranty_months,
        brand, model, tax_in_code
        """
        self._init_payload(count=1, update_product=False, update_variant=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        skus = models.SellableProduct.query.all()
        for sku in skus:
            self.assertEqual(sku.category_id, self.payload['categoryId'])
            self.assertEqual(sku.master_category_id, self.payload['masterCategoryId'])
            self.assertEqual(sku.provider_id, self.payload['providerId'])
            self.assertEqual(sku.warranty_months, self.payload['warrantyMonths'])
            self.assertEqual(sku.brand_id, self.payload['brandId'])
            self.assertEqual(sku.model, self.payload['model'])
            self.assertEqual(sku.tax_in_code, self.payload['taxInCode'])

    def test_withProductFields_withProductId_return200_updateForAllSku(self):
        self._init_payload(count=1, update_product=False, update_variant=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)

        self.payload['categoryId'] = fake.category(is_active=True, seller_id=self.payload['sellerId']).id
        self.payload['masterCategoryId'] = fake.master_category(is_active=True).id
        self.payload['providerId'] = 2
        self.payload['warrantyMonths'] = fake.integer(max=12)
        self.payload['brandId'] = fake.brand().id
        self.payload['model'] = fake.text()
        self.payload['taxInCode'] = fake.tax(code='0').code
        self.payload['productId'] = body['result'].get('productId')

        del self.payload['variants'][0]['uomId']
        del self.payload['variants'][0]['attributes']
        del self.payload['variants'][0]['uomRatio']
        self.payload['variants'][0]['variantId'] = body['result']['variants'][0]['variantId']
        self.payload['variants'][0]['sku']['sku'] = body['result']['variants'][0]['sku']

        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)
        skus = models.SellableProduct.query.all()
        for sku in skus:
            self.assertEqual(sku.category_id, self.payload['categoryId'])
            self.assertEqual(sku.master_category_id, self.payload['masterCategoryId'])
            self.assertEqual(sku.provider_id, self.payload['providerId'])
            self.assertEqual(sku.warranty_months, self.payload['warrantyMonths'])
            self.assertEqual(sku.brand_id, self.payload['brandId'])
            self.assertEqual(sku.model, self.payload['model'])
            self.assertEqual(sku.tax_in_code, self.payload['taxInCode'])

    def test_createProduct_2variants_withDuplicatedSellerSku_return400(self):
        self._init_payload(
            is_variation=1, count=1,
            update_product=False, update_variant=False, update_sku=False,
            seller_sku='sellerSku'
        )

        self.payload['variants'][1]['uomId'] = self.payload['variants'][0]['uomId']
        self.payload['variants'][1]['uomRatio'] = self.payload['variants'][0]['uomRatio']
        self.payload['variants'][1]['attributes'] = [{
            'id': self.attributes[0].id,
            'value': str(self.attribute_options[0].id)
        }, {
            'id': self.attributes[1].id,
            'value': str(self.attribute_options[3].id)
        }]
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 400, body)
        self.assertEqual(body['message'], f'Sản phẩm sellerSku đã tồn tại')

    def test_updateProduct_newVariant_withDuplicatedSellerSku_return400(self):
        self._init_payload(is_variation=1, count=1, update_variant=False, update_sku=False)
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 200)
        for i in range(len(self.payload['variants'])):
            del self.payload['variants'][i]['uomId']
            del self.payload['variants'][i]['attributes']
            del self.payload['variants'][i]['uomRatio']
            self.payload['variants'][i]['variantId'] = body['result']['variants'][i]['variantId']
            self.payload['variants'][i]['sku']['sku'] = body['result']['variants'][i]['sku']

        for i in range(len(self.uom_attr_options)):
            variant = {
                'uomId': self.uom_attr_options[i].id,
                'uomRatio': self.ratio_attr_options[i].value,
                'attributes': [{
                    'id': self.attributes[0].id,
                    'value': str(self.attribute_options[1].id)
                }, {
                    'id': self.attributes[1].id,
                    'value': str(self.attribute_options[2].id)
                }],
                'sku': {
                    'images': [],
                    'trackingType': False,
                    'expiryTracking': True,
                    'expirationType': random.choice([1, 2]),
                    'daysBeforeExpLock': fake.integer(),
                    'productType': random.choice(['product', 'consu']),
                    'sellerSku': self.payload['variants'][0]['sku']['sellerSku']
                }
            }
            self.payload['variants'].append(variant)
        code, body = self.call_api(self.payload)
        self.assertEqual(code, 400, body)
        self.assertEqual(body['message'], f'Sản phẩm {self.payload["variants"][0]["sku"]["sellerSku"]} đã tồn tại')


class TestUpdateProductModel(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1244'
    FOLDER = '/Sku/CreateListSku/UpdateModel'

    def url(self):
        return '/create_list_sku'

    def method(self):
        return 'POST'

    def setUp(self):
        fake.init_editing_status()
        self.created_by = 'quanglm'
        self.attribute_set = fake.attribute_set()
        self.category = fake.category(is_active=True)
        self.product = fake.product(category_id=self.category.id, attribute_set_id=self.attribute_set.id)
        self.skus = []
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self):
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def __add_sku(self):
        number_skus = random.randint(10, 20)
        for i in range(number_skus):
            product_variant = fake.product_variant(
                product_id=self.product.id
            )
            sku = fake.sellable_product(variant_id=product_variant.id)
            self.skus.append(sku)

    def __init_sku_update(self):
        self.__add_sku()
        self.payload['variants'] = [{
            'variantId': self.skus[0].variant_id,
            'sku': {
                'sku': self.skus[0].sku,
                'barcodes': [fake.text(30)],
                'sellerSku': fake.text()
            }
        }]

    def __init_sku_create(self):
        self.__add_sku()
        product_variant = fake.product_variant(
            product_id=self.product.id
        )
        self.payload['variants'] = [{
            'variantId': product_variant.id,
            'sku': {
                'trackingType': False,
                'expiryTracking': False,
                'daysBeforeExpLock': fake.integer(),
                'productType': random.choice(['product', 'consu']),
                'sellerSku': fake.text()
            }
        }]

    def _init_payload(self, model):
        self.payload = {
            'sellerId': self.category.seller_id,
            'createdBy': self.created_by,
            'productId': self.product.id,
            'model': model
        }
        return

    def __assert_model(self, model):
        product = models.Product.query.filter(models.Product.id == self.product.id).first()
        skus = models.SellableProduct.query.filter(models.SellableProduct.product_id == self.product.id).all()

        self.assertEqual(model, product.model)
        for sku in skus:
            self.assertEqual(model, sku.model)

    def testCreateListSKu_test_return200_with_only_update_product_model_updateAllSku(self):
        model = fake.text()
        self._init_payload(model)
        self.__add_sku()
        code, body = self.call_api(self.payload)

        self.assertEqual(200, code, body)
        self.__assert_model(model)

    def testCreateListSKu_test_return200_with_update_product_model_with_update_sku_updateAllSku(self):
        model = fake.text()
        self._init_payload(model)
        self.__init_sku_update()
        code, body = self.call_api(self.payload)

        self.assertEqual(200, code, body)
        self.__assert_model(model)

    def testCreateListSKu_test_return200_with_update_product_model_with_create_sku_updateAllSku(self):
        model = fake.text()
        self._init_payload(model)
        self.__init_sku_create()
        code, body = self.call_api(self.payload)

        self.assertEqual(200, code, body)
        self.__assert_model(model)


class TestCreateSkuWithAttribute(TestCreateListSKuLayerSKU):
    ISSUE_KEY = 'CATALOGUE-1256'
    FOLDER = '/Sku/CreateListSku/SkuLayer'

    def url(self):
        return 'create_list_sku'

    def method(self):
        return 'POST'

    def setUp(self) -> None:
        fake.init_editing_status()
        self.created_by = 'long.t'
        self.seller = fake.seller()
        self.master_category = fake.master_category(is_active=True)
        self.brand = fake.brand()
        self.tax = fake.tax(code="10")
        current_app.config.update(INTERNAL_HOST_URLS=['localhost'])

    def tearDown(self) -> None:
        current_app.config.update(INTERNAL_HOST_URLS=[])

    def _init_attribute_set(self, is_variation=1):
        self.attribute_set = fake.attribute_set()
        attribute_group = fake.attribute_group(
            set_id=self.attribute_set.id,
            system_group=False
        )
        self.attributes = [
            fake.attribute(
                code='s' + str(i),
                value_type='selection',
                is_none_unit_id=True
            ) for i in range(1, 4)
        ]

        self.attribute_options = []

        for i in range (0, len(self.attributes)):
            self.attribute_options.append([
                fake.attribute_option(self.attributes[i].id),
                fake.attribute_option(self.attributes[i].id),
            ])
            fake.attribute_group_attribute(
                attribute_id=self.attributes[i].id,
                group_ids=[attribute_group.id],
                is_variation=is_variation
            )

    def _init_variants(self, is_variation=False, count=1, update=True):
        self.payload_variants = []
        for value_1 in range(2):
            for value_2 in range(2):
                for value_3 in range(2):
                    variant = {
                        'uomId': self.uom_attr_options[0].id,
                        'uomRatio': self.ratio_attr_options[0].value,
                        'attributes': [{
                            'id': self.attributes[0].id,
                            'value': str(self.attribute_options[0][value_1].id)
                        }, {
                            'id': self.attributes[1].id,
                            'value': str(self.attribute_options[1][value_2].id)
                        }, {
                            'id': self.attributes[2].id,
                            'value': str(self.attribute_options[2][value_3].id)
                        }]
                    }
                    self.payload_variants.append(variant)

    def testCreateListSku_test_with_all_attributes_in_attribute_set_return_200_with_sku_created(self):
        self._init_payload(
            is_variation=1, count=3,
            update_product=False, update_variant=False, update_sku=False
        )
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)

    def testCreateListSku_test_with_some_attributes_in_attribute_set_return_200_with_sku_created(self):
        self._init_payload(
            is_variation=1, count=2,
            update_product=False, update_variant=False, update_sku=False
        )
        self.payload_variants = []
        for value_1 in range(2):
            for value_2 in range(2):
                variant = {
                    'uomId': self.uom_attr_options[0].id,
                    'uomRatio': self.ratio_attr_options[0].value,
                    'attributes': [{
                        'id': self.attributes[0].id,
                        'value': str(self.attribute_options[0][value_1].id)
                    }, {
                        'id': self.attributes[1].id,
                        'value': str(self.attribute_options[1][value_2].id)
                    }]
                }
                self.payload_variants.append(variant)
        self.payload.update({'variants': self.payload_variants})
        code, body = self.call_api(self.payload)
        self.assertEqual(200, code, body)

    def testCreateListSku_test_with_different_attribute_between_sku_return_400_validate_error(self):
        self._init_payload(
            is_variation=1, count=2,
            update_product=False, update_variant=False, update_sku=False
        )
        self.payload_variants = []
        for value_1 in range(2):
            for value_2 in range(2):
                variant = {
                    'uomId': self.uom_attr_options[0].id,
                    'uomRatio': self.ratio_attr_options[0].value,
                    'attributes': [{
                        'id': self.attributes[0].id,
                        'value': str(self.attribute_options[0][value_1].id)
                    }, {
                        'id': self.attributes[1].id,
                        'value': str(self.attribute_options[1][value_2].id)
                    }]
                }
                if value_1 == 1 and value_2 == 1:
                    variant = {
                        'uomId': self.uom_attr_options[0].id,
                        'uomRatio': self.ratio_attr_options[0].value,
                        'attributes': [{
                            'id': self.attributes[0].id,
                            'value': str(self.attribute_options[0][value_1].id)
                        }, {
                            'id': self.attributes[1].id,
                            'value': str(self.attribute_options[1][value_2].id)
                        }, {
                            'id': self.attributes[2].id,
                            'value': str(self.attribute_options[2][0].id)
                        }]
                    }
                self.payload_variants.append(variant)

        self.payload.update({'variants': self.payload_variants})
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, body)
        self.assertEqual('2 biến thể có các thuộc tính biến thể khác nhau', body['message'])

    def testCreateListSku_test_with_same_attribute_same_value_between_sku_return_400_validate_error(self):
        self._init_payload(
            is_variation=1, count=2,
            update_product=False, update_variant=False, update_sku=False
        )
        self.payload_variants = []
        for value_1 in range(2):
            for value_2 in range(2):
                variant = {
                    'uomId': self.uom_attr_options[0].id,
                    'uomRatio': self.ratio_attr_options[0].value,
                    'attributes': [{
                        'id': self.attributes[0].id,
                        'value': str(self.attribute_options[0][value_1].id)
                    }, {
                        'id': self.attributes[1].id,
                        'value': str(self.attribute_options[1][value_2].id)
                    }]
                }
                if value_1 == 0 and value_2 == 1:
                    variant = {
                        'uomId': self.uom_attr_options[0].id,
                        'uomRatio': self.ratio_attr_options[0].value,
                        'attributes': [{
                            'id': self.attributes[0].id,
                            'value': str(self.attribute_options[0][value_1].id)
                        }, {
                            'id': self.attributes[1].id,
                            'value': str(self.attribute_options[1][value_1].id)
                        }]
                    }
                self.payload_variants.append(variant)
        self.payload.update({'variants': self.payload_variants})
        code, body = self.call_api(self.payload)
        self.assertEqual(400, code, body)
        self.assertEqual('Tồn tại biến thể trùng lặp', body['message'])
