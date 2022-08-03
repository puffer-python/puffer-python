# coding=utf-8
import random
from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user
from catalog import models


class GetGenericProductsTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1609'
    FOLDER = '/Products/Get_products'

    NUMBER_OF_PRODUCTS = 20
    MAX_NUMBER_OF_VARIANTS = 10
    MAX_NUMBER_OF_ATTRIBUTES = 10
    MAX_NUMBER_OF_MASTER_CATEGORIES = 4
    MAX_NUMBER_OF_CATEGORIES = 10

    def setUp(self):

        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.attribute = fake.attribute(value_type='selection')
        self.option = fake.attribute_option(
            attribute_id=self.attribute.id,
            seller_id=self.user.seller_id,
        )

        self.master_categories = [fake.master_category(
            parent_id=fake.master_category(is_active=True).id,
            is_active=True
        ) for _ in range(self.MAX_NUMBER_OF_MASTER_CATEGORIES)]

        self.categories = [fake.category(
            seller_id=self.seller.id,
            master_category_id=self.master_categories[random.randrange(0, self.MAX_NUMBER_OF_MASTER_CATEGORIES)].id
        ) for _ in range(self.MAX_NUMBER_OF_CATEGORIES)]

        self.attribute_set = fake.attribute_set()

        uom_attribute_group = fake.attribute_group(set_id=self.attribute_set.id)
        self.uom_attr = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        self.uom_ratio_attr = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids=[uom_attribute_group.id],
            is_variation=1
        )
        self.attr_option_cai = fake.attribute_option(self.uom_attr.id, value='Cái')
        self.attr_option_chiec = fake.attribute_option(self.uom_attr.id, value='Chiếc')
        self.attr_option_1 = fake.attribute_option(self.uom_ratio_attr.id, value='1')

        self.products = []
        self.product_names = []

        for _ in range(self.NUMBER_OF_PRODUCTS):
            product = fake.product(created_by=self.user.email, category_id=self.categories[random.randrange(0, self.MAX_NUMBER_OF_CATEGORIES)].id, model=fake.text(10))
            self.products.append(product)
            self.product_names.append(product.name)
            for _ in range(random.randrange(1, self.MAX_NUMBER_OF_VARIANTS)):
                product_variant = fake.product_variant(product_id=product.id, uom_attr=self.uom_attr,
                                                       uom_option_value=self.attr_option_cai.id,
                                                       uom_ratio_attr=self.uom_ratio_attr,
                                                       uom_ratio_value=self.attr_option_1.value)
                fake.sellable_product(variant_id=product_variant.id, seller_id=self.seller.id)

    def method(self):
        return 'GET'

    def url(self):
        return '/products'
    
    def build_url(self, data):
        prefix = '/products?'
        params = []
        for k, v in data.items():
           params.append(f'{k}={v}')
        return prefix + '&'.join(params)

    def assert_product(self, product_dict):
        product_id = product_dict["id"]
        product_from_db = models.Product.query.get(product_id)
        assert product_from_db is not None
        assert len(product_from_db.sellable_products) == len(product_dict["variants"])
        assert product_dict["name"] == product_from_db.name
        assert product_dict["model"] == product_from_db.model
        assert product_dict["brandId"] == product_from_db.brand_id
        assert product_dict["brandName"] == product_from_db.brand.name
        for variant, sellable_product in zip(product_dict["variants"], product_from_db.sellable_products):
            assert variant["sku"] == sellable_product.sku
            assert variant["variantId"] == sellable_product.variant_id
            assert variant["sellerSku"] == sellable_product.seller_sku
            assert variant["sellerCategoryId"] == sellable_product.category_id
            assert variant["sellerCategoryFullPathName"] == sellable_product.category.full_path
            assert len(variant["variantAttributes"]) == len(sellable_product.product_variant.variation_attributes)
            for variant_attribute, variant_attribute_from_db in zip(variant["variantAttributes"], sellable_product.product_variant.variation_attributes):
                assert variant_attribute["attributeId"] == variant_attribute_from_db.attribute_id
                assert variant_attribute["attributeName"] == variant_attribute_from_db.attribute.display_name
                assert variant_attribute["attributeOptionId"] == variant_attribute_from_db.attribute_option.id
                assert variant_attribute["attributeOptionValue"] == variant_attribute_from_db.attribute_option.value

    def assert_products(self, products):
        for product in products:
            self.assert_product(product)

    def detructure(self, body):
        return (body["result"]["totalRecords"], body["result"]["pageSize"], body["result"]["currentPage"], body["result"]["products"])

    def test_get_products_without_params_return_200(self):
        with logged_in_user(self.user):
            code, body = self.call_api()
            assert code == 200
            total_record, page_size, current_page, products = self.detructure(body)
            products_from_db = models.Product.query.filter().all()
            total_records_from_db = len(products_from_db)
            assert page_size == len(products)
            assert total_record == total_records_from_db
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)

    def test_products_with_page_size_return_200(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "page": 1,
                "pageSize": 5
            }))
            assert code == 200
            total_record, page_size, current_page, products = self.detructure(body)
            products_from_db = models.Product.query.filter().all()
            total_records_from_db = len(products_from_db)
            assert page_size == len(products)
            assert total_record == total_records_from_db
            assert page_size == 5
            assert current_page == 1
            self.assert_products(products=products)
    
    def test_get_products_with_specific_page_return_200(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "page": 2,
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            products_from_db = models.Product.query.filter().all()
            total_records_from_db = len(products_from_db)
            assert page_size == len(products)
            assert total_record == total_records_from_db
            assert page_size == 10
            assert current_page == 2
            self.assert_products(products=products)
    

    def test_get_products_with_keywords_return_200(self):
        prefix_search = fake.text(3)
        products_from_db = models.Product.query.filter().all()
        new_names = []
        for index in range(10):
            new_name = prefix_search + fake.text(4)
            new_names.append(new_name)
            product = products_from_db[index]
            product.name = new_name
        models.db.session.commit()

        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "keyword": prefix_search,
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 10
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_products_with_single_model_return_200_with_a_product(self):
        model = self.products[0].model
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url({
                    "models": model
                })
            )
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 1
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)
    
    def test_get_products_with_multiple_model_return_200_with_multiple_products(self):
        model = ",".join([self.products[0].model, self.products[1].model, self.products[2].model])
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url({
                    "models": model
                })
            )
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 3
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)
    
    def test_get_products_with_multiple_model_return_200_with_single_product(self):
        model = ",".join([self.products[0].model, self.products[0].model, self.products[0].model])
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url({
                    "models": model
                })
            )
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 1
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_products_with_single_model_return_200_with_no_product(self):
        model = ",".join([fake.text(10)])
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url({
                    "models": model
                })
            )
            total_record, page_size, current_page, _ = self.detructure(body)
            assert code == 200
            assert total_record == 0
            assert page_size == 10
            assert current_page == 1
    
    def test_get_products_with_multiple_model_return_200_with_no_product(self):
        models = ",".join([fake.text(10), fake.text(10), fake.text(10)])
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url({
                    "models": models
                })
            )
            total_record, page_size, current_page, _ = self.detructure(body)
            assert code == 200
            assert total_record == 0
            assert page_size == 10
            assert current_page == 1

    def test_get_products_with_model_and_keyword_return_200_with_a_product(self):
        prefix_search = fake.text(3)
        product = models.Product.query.filter().first()
        product.name = prefix_search + fake.text(3)
        models.db.session.commit()
        data = {
            "models": product.model,
            "keyword": prefix_search
        }
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url(data)
            )
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 1
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_products_with_models_and_keyword_return_200_with_multiple_products(self):
        prefix_search = fake.text(3)
        _products = models.Product.query.filter().all()
        _products[0].name = prefix_search + fake.text(3)
        _products[1].name = prefix_search + fake.text(3)
        _products[2].name = prefix_search + fake.text(3)
        models.db.session.commit()
        data = {
            "models": ",".join([_products[0].model, _products[1].model, _products[2].model]),
            "keyword": prefix_search
        }
        with logged_in_user(self.user):
            code, body = self.call_api(
                url=self.build_url(data)
            )
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 3
            assert page_size == 10
            assert current_page == 1
            self.assert_products(products=products)
    
    def test_get_products_without_login_return_401(self):
        code, body = self.call_api()
        assert body["code"] == "INVALID"
        assert body["message"] == "Unauthorized error"
        assert body["result"] == None
        assert code == 401

    def test_get_products_with_unknow_params_return_400(self):
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "port": 3000
            }))
            assert body["code"] == "INVALID"
            assert body["message"] == "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại"
            assert code == 400

    def test_get_product_with_all_params_return_200_with_a_product(self):
        prefix_search = fake.text(3)
        _products = models.Product.query.filter().all()
        _products[0].name = prefix_search + fake.text(3)
        _products[1].name = prefix_search + fake.text(3)
        _products[2].name = prefix_search + fake.text(3)
        models.db.session.commit()
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "page": 1,
                "pageSize": 1,
                "keyword": prefix_search,
                "models": ",".join([_products[0].model, _products[1].model, _products[2].model])
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 3
            assert page_size == 1
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_product_with_all_params_return_200_with_multiple_products(self):
        prefix_search = fake.text(3)
        _products = models.Product.query.filter().all()
        _products[0].name = prefix_search + fake.text(3)
        _products[1].name = prefix_search + fake.text(3)
        _products[2].name = prefix_search + fake.text(3)
        models.db.session.commit()
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "page": 1,
                "pageSize": 3,
                "keyword": prefix_search,
                "models": ",".join([_products[0].model, _products[1].model, _products[2].model]),
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 3
            assert page_size == 3
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_product_with_all_params_with_diffrent_sellerId_return_200_with_no_products(self):
        prefix_search = fake.text(3)
        _products = models.Product.query.filter().all()
        _products[0].name = prefix_search + fake.text(3)
        _products[1].name = prefix_search + fake.text(3)
        _products[2].name = prefix_search + fake.text(3)
        models.db.session.commit()
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "page": 1,
                "pageSize": 3,
                "keyword": prefix_search,
                "models": ",".join([_products[0].model, _products[1].model, _products[2].model]),
                "sellerId": self.seller.id + 1
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 0
            assert page_size == 3
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_product_with_all_params_with_sellerId_return_200_with_muliple_products(self):
        with logged_in_user(self.user):
            _products = models.Product.query.filter().order_by(models.Product.name).all()
            code, body = self.call_api(url=self.build_url({
                "page": 1,
                "pageSize": 3,
                "sellerId": self.seller.id
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == len(_products)
            assert page_size == 3
            assert current_page == 1
            self.assert_products(products=products)

    def test_get_product_with_all_params_witht_sellerId_and_keyword_return_200_with_multiple_products(self):
        prefix_search = fake.text(3)
        _products = models.Product.query.filter().all()
        _products[0].name = prefix_search + fake.text(3)
        _products[1].name = prefix_search + fake.text(3)
        _products[2].name = prefix_search + fake.text(3)
        models.db.session.commit()
        with logged_in_user(self.user):
            code, body = self.call_api(url=self.build_url({
                "page": 1,
                "pageSize": 3,
                "keyword": prefix_search,
                "sellerId": self.seller.id
            }))
            total_record, page_size, current_page, products = self.detructure(body)
            assert code == 200
            assert total_record == 3
            assert page_size == 3
            assert current_page == 1
            self.assert_products(products=products)

    
    def test_get_product_with_all_params_with_sellerId_and_models_return_200_with_multiple_products(self):
            prefix_search = fake.text(3)
            _products = models.Product.query.filter().all()
            _products[0].name = prefix_search + fake.text(3)
            _products[1].name = prefix_search + fake.text(3)
            _products[2].name = prefix_search + fake.text(3)
            models.db.session.commit()
            with logged_in_user(self.user):
                code, body = self.call_api(url=self.build_url({
                    "page": 1,
                    "pageSize": 3,
                    "keyword": prefix_search,
                    "models": ",".join([_products[0].model, _products[1].model, _products[2].model]),
                    "sellerId": self.seller.id
                }))
                total_record, page_size, current_page, products = self.detructure(body)
                assert code == 200
                assert total_record == 3
                assert page_size == 3
                assert current_page == 1
                self.assert_products(products=products)