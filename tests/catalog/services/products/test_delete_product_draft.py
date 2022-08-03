#coding=utf-8

from catalog.services.products import ProductService
from catalog import models
from tests.faker import fake
from tests.catalog.api import APITestCase


service = ProductService.get_instance()

class DeleteDraftProductTestCase(APITestCase):
    ISSUE_KEY = 'SC-447'

    def test_deleteAllResourceOfProduct__whenProductExist(self):
        user = fake.iam_user()
        product = fake.product(created_by=user.email, editing_status_code='draft')
        variant = fake.product_variant(product_id=product.id)
        image = fake.variant_product_image(variant.id)
        service.delete_draft_product(user.email)
        assert models.Product.query.get(product.id) == None
        assert models.ProductVariant.query.get(variant.id) == None
        assert models.VariantImage.query.get(image.id) == None

    def test_dontRaiseError__whenProductNotExist(self):
        user = fake.iam_user()
        service.delete_draft_product(user.email)

    def test_dontRaiseError__whenProductOwnedByOtherUser(self):
        user = fake.iam_user()
        product = fake.product(created_by=fake.iam_user().email, editing_status_code='draft')
        variant = fake.product_variant(product_id=product.id)
        image = fake.variant_product_image(variant.id)
        service.delete_draft_product(user.email)
        assert models.Product.query.get(product.id) == product
        assert models.ProductVariant.query.get(variant.id) == variant
        assert models.VariantImage.query.get(image.id) == image
