from tests import logged_in_user
from tests.faker import fake
from tests.catalog.api import APITestCase
from catalog import models
from sqlalchemy import func


class TestMoveSKU(APITestCase):
    ISSUE_KEY = "CATALOGUE-1481"
    FOLDER = "/Sku/UpdateSku/MoveSkus"

    def method(self):
        return "PUT"

    def url(self):
        return "/skus"

    def call_api(self, **kwargs):
        with logged_in_user(self.user):
            return super().call_api(**kwargs)

    def check_products(self, products, product_id):
        for product in products:
            assert product["productId"] == product_id

    def get_max_seller_id(self):
        return models.db.session.query(func.max(models.Category.id)).scalar() or 0

    def get_max_product_id(self):
        return models.db.session.query(func.max(models.Product.id)).scalar() or 0

    def check_products_from_db(self, skus, product_id):
        product = models.Product.query.get(product_id)

        sellable_products = models.SellableProduct.query.filter(
            models.SellableProduct.sku.in_(skus)
        ).all()
        target_sellable_product = models.SellableProduct.query.filter(
            models.SellableProduct.product_id == product_id
        ).first()

        target_variant_attributes = models.VariantAttribute.query.filter(
            models.VariantAttribute.variant_id == target_sellable_product.variant_id
        ).order_by(
            models.VariantAttribute.attribute_id
        ).all()

        for sellable in sellable_products:
            assert sellable.product_id == product_id
            assert sellable.category_id == product.category_id
            assert sellable.model == product.model
            variants = models.ProductVariant.query.filter(
                        models.ProductVariant.product_id == sellable.product_id
            ).all()

            for variant in variants:
                assert variant.product_id == product_id
                assert sellable.category_id == product.category_id
                assert sellable.attribute_set_id == product.attribute_set_id

                variant_attributes = models.VariantAttribute.query.filter(
                    models.VariantAttribute.variant_id == variant.id
                ).order_by(
                    models.VariantAttribute.attribute_id
                ).all()
                assert len(variant_attributes) == len(target_variant_attributes)
                for target_variant_attribute, moved_variant_attribute in zip(target_variant_attributes, variant_attributes):
                    assert target_variant_attribute.attribute_id == moved_variant_attribute.attribute_id

    def setUp(self):
        self.fake_attribute_set()
        self.meta_data_set_up()
        self.max = 10
        self.products = []
        
        self.iphone_13 = fake.product(category_id=self.digital_category.id, brand_id = self.apple_brand.id, 
            attribute_set_id=self.attribute_set_1.id, model='IPhone')

        self.iphone_12 = fake.product(category_id=self.digital_category.id, brand_id = self.apple_brand.id, 
            attribute_set_id=self.attribute_set_1.id, model='IPhone')

        self.cloth = fake.product(category_id=self.cloth_category.id, brand_id = self.boo_brand.id, 
            attribute_set_id=self.attribute_set_2.id, model='Boo')

        self.iphone_14 = fake.product(category_id=self.digital_category.id, brand_id = self.apple_brand.id, 
            attribute_set_id=self.attribute_set_1.id, model='IPhone')
        
        # iphone13 mini red attribute
        iphone13_mini_red = fake.product_variant(product_id=self.iphone_13.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_cai.id, uom_ratio_value=self.attr_option_1.value)
        fake.variant_attribute(variant_id=iphone13_mini_red.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=iphone13_mini_red.id, attribute_id=self.color_attribute.id, value='Red')
        self.iphone13_mini_red = fake.sellable_product(seller_id= self.seller.id, variant_id=iphone13_mini_red.id, uom_ratio=self.attr_option_1.value, uom_code=self.attr_option_cai.code)

        # iphone13 mini green attribute
        iphone13_mini_green = fake.product_variant(product_id=self.iphone_13.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_cai.id, uom_ratio_value=self.attr_option_1.value)
        fake.variant_attribute(variant_id=iphone13_mini_green.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=iphone13_mini_green.id, attribute_id=self.color_attribute.id, value='Green')
        self.iphone13_mini_green = fake.sellable_product(seller_id= self.seller.id, variant_id=iphone13_mini_green.id, uom_ratio=self.attr_option_1.value, uom_code=self.attr_option_cai.code)

        #thung iphone13 mini green attribute
        thung_iphone13_mini_green = fake.product_variant(product_id=self.iphone_13.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_thung.id, uom_ratio_value=self.attr_option_10.value)
        fake.variant_attribute(variant_id=thung_iphone13_mini_green.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=thung_iphone13_mini_green.id, attribute_id=self.color_attribute.id, value='Green')
        self.thung_iphone13_mini_green = fake.sellable_product(seller_id= self.seller.id, variant_id=thung_iphone13_mini_green.id, uom_ratio=self.attr_option_10.value, uom_code=self.attr_option_thung.code)

        # iphone12 mini green attribute
        iphone12_mini_green = fake.product_variant(product_id=self.iphone_12.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_cai.id, uom_ratio_value=self.attr_option_1.value)
        fake.variant_attribute(variant_id=iphone12_mini_green.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=iphone12_mini_green.id, attribute_id=self.color_attribute.id, value='Green')
        self.iphone12_mini_green = fake.sellable_product(seller_id= self.seller.id, variant_id=iphone12_mini_green.id)

        # iphone12 mini blue attribute
        iphone12_mini_blue = fake.product_variant(product_id=self.iphone_12.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_cai.id, uom_ratio_value=self.attr_option_1.value)
        fake.variant_attribute(variant_id=iphone12_mini_blue.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=iphone12_mini_blue.id, attribute_id=self.color_attribute.id, value='Blue')
        self.iphone12_mini_blue = fake.sellable_product(seller_id= self.seller.id, variant_id=iphone12_mini_blue.id, uom_ratio=self.attr_option_1.value, uom_code=self.attr_option_cai.code)

        # thung iphone12 mini green attribute
        thung_iphone12_mini_green = fake.product_variant(product_id=self.iphone_12.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_thung.id, uom_ratio_value=self.attr_option_10.value)
        fake.variant_attribute(variant_id=thung_iphone12_mini_green.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=thung_iphone12_mini_green.id, attribute_id=self.color_attribute.id, value='Green')
        self.thung_iphone12_mini_green = fake.sellable_product(seller_id= self.seller.id, variant_id=thung_iphone12_mini_green.id, uom_ratio=self.attr_option_10.value, uom_code=self.attr_option_thung.code)

        # thung iphone12 mini blue attribute
        thung_iphone12_mini_blue = fake.product_variant(product_id=self.iphone_12.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_thung.id, uom_ratio_value=self.attr_option_10.value)
        fake.variant_attribute(variant_id=thung_iphone12_mini_blue.id, attribute_id=self.size_attribute.id, value='5x15')
        fake.variant_attribute(variant_id=thung_iphone12_mini_blue.id, attribute_id=self.color_attribute.id, value='Blue')
        self.thung_iphone12_mini_blue = fake.sellable_product(seller_id= self.seller.id, variant_id=thung_iphone12_mini_blue.id, uom_ratio=self.attr_option_10.value, uom_code=self.attr_option_thung.code)

        #update all_uom_ratio
        _iphone13_mini_red = models.ProductVariant.query.get(iphone13_mini_red.id)
        _iphone13_mini_red.all_uom_ratios = f"{_iphone13_mini_red.id}:1.0,"
        _iphone13_mini_green = models.ProductVariant.query.get(iphone13_mini_green.id)
        _iphone13_mini_green.all_uom_ratios = f"{_iphone13_mini_green.id}:1.0,{self.thung_iphone13_mini_green.id}:10.0"
        _thung_iphone13_mini_green = models.ProductVariant.query.get(thung_iphone13_mini_green.id)
        _thung_iphone13_mini_green.all_uom_ratios = f"{_thung_iphone13_mini_green.id}:1.0,{self.thung_iphone13_mini_green.id}:10.0"

        _iphone12_mini_blue = models.ProductVariant.query.get(iphone12_mini_blue.id)
        _iphone12_mini_blue.all_uom_ratios =  f"{_iphone12_mini_blue.id}:1.0,{self.thung_iphone12_mini_blue.id}:10.0"
        _iphone12_mini_green = models.ProductVariant.query.get(iphone12_mini_green.id)
        _iphone12_mini_green.all_uom_ratios = f"{_iphone12_mini_green.id}:1.0,{self.thung_iphone12_mini_green.id}:10.0"
        _thung_iphone12_mini_green = models.ProductVariant.query.get(thung_iphone12_mini_green.id)
        _thung_iphone12_mini_green.all_uom_ratios = f"{_iphone12_mini_green.id}:1.0,{self.thung_iphone12_mini_green.id}:10.0"
        _thung_iphone12_mini_blue = models.ProductVariant.query.get(thung_iphone12_mini_blue.id)
        _thung_iphone12_mini_blue.all_uom_ratios = f"{_iphone12_mini_blue.id}:1.0,{self.thung_iphone12_mini_blue.id}:10.0"

        # Black T shirt - XL
        black_t_shirt_XL = fake.product_variant(product_id=self.cloth.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_chiec.id, uom_ratio_value=self.attr_option_1.value)
        fake.variant_attribute(variant_id=black_t_shirt_XL.id, attribute_id=self.size_attribute.id, value='XL')
        fake.variant_attribute(variant_id=black_t_shirt_XL.id, attribute_id=self.color_attribute.id, value='Blue')
        fake.variant_attribute(variant_id=black_t_shirt_XL.id, attribute_id=self.material_attribute.id, value='leather')
        self.black_t_shirt = fake.sellable_product(seller_id= self.seller.id, variant_id=black_t_shirt_XL.id, uom_ratio=self.attr_option_10.value, uom_code=self.attr_option_thung.code)
        _black_t_shirt_XL = models.ProductVariant.query.get(black_t_shirt_XL.id)
        #Thung Black Tshirt XL
        thung_black_t_shirt_XL = fake.product_variant(product_id=self.cloth.id, uom_attr=self.unit_attribute, uom_option_value=self.attr_option_thung.id, uom_ratio_value=self.attr_option_10.value)
        fake.variant_attribute(variant_id=thung_black_t_shirt_XL.id, attribute_id=self.size_attribute.id, value='XL')
        fake.variant_attribute(variant_id=thung_black_t_shirt_XL.id, attribute_id=self.color_attribute.id, value='Blue')
        fake.variant_attribute(variant_id=thung_black_t_shirt_XL.id, attribute_id=self.material_attribute.id, value='leather')
        self.black_t_shirt = fake.sellable_product(seller_id= self.seller.id, variant_id=thung_black_t_shirt_XL.id, uom_ratio=self.attr_option_10.value, uom_code=self.attr_option_thung.code)
        _thung_black_t_shirt_XL = models.ProductVariant.query.get(thung_black_t_shirt_XL.id)
        _thung_black_t_shirt_XL.all_uom_ratios = f"{_thung_black_t_shirt_XL.id}:1.0,{_thung_black_t_shirt_XL.id}:10.0"
        _black_t_shirt_XL.all_uom_ratios = f"{_thung_black_t_shirt_XL.id}:1.0,{_thung_black_t_shirt_XL.id}:10.0"

        models.db.session.commit()

    def meta_data_set_up(self):
        # ======================== Create foo Seller =====================
        self.seller = fake.seller()
        # ======================== Create foo User =======================
        self.user = fake.iam_user(seller_id=self.seller.id)
        # ======================== Create Apple Band =====================
        self.apple_brand = fake.brand(hasLogo=False)
        # ======================== Create Boo Band =======================
        self.boo_brand = fake.brand(hasLogo=False)
        # ===================== Create cloth attribute set ===============
        self.fake_attribute_set()
        # =========================== create digital category ============================
        self.digital_category = fake.category(is_active=True, attribute_set_id = self.attribute_set_1.id, seller_id=self.seller.id)
        # =========================== create cloth category ============================
        self.cloth_category = fake.category(is_active=True, attribute_set_id = self.attribute_set_2.id, seller_id=self.seller.id)
        # =========================== create mobile category ============================
        self.mobile_category = fake.category(is_active=True, attribute_set_id = self.attribute_set_1.id, seller_id=self.seller.id)

    def add_attribute_to_product(self, product_id, attribute_id, value):
        variants = models.ProductVariant.query.filter(
            models.ProductVariant.product_id == product_id
        ).all()
        for variant in variants:
            #check attribute already exist
            variant_attribute = models.VariantAttribute.query.filter(
                models.VariantAttribute.attribute_id == attribute_id,
                models.VariantAttribute.variant_id == variant.id
            ).first()
            if variant_attribute:
                assert False
            fake.variant_attribute(variant_id=variant.id, attribute_id=attribute_id, value=value)
        
    def fake_attribute_set(self, **kwargs):
        self.attribute_set_1 = fake.attribute_set(**kwargs)
        self.attribute_set_2 = fake.attribute_set(**kwargs)

        self.attribute_group_1 = fake.attribute_group(set_id=self.attribute_set_1.id)
        self.attribute_group_2 = fake.attribute_group(set_id=self.attribute_set_2.id)

        self.unit_attribute = fake.attribute(
            code='uom',
            value_type='selection',
            group_ids = [self.attribute_group_1.id],
            is_variation = 1
        )

        self.size_attribute = fake.attribute(
            code='size',
            value_type='text',
            group_ids = [self.attribute_group_1.id],
            is_variation = 1
        )

        self.color_attribute = fake.attribute(
            code='color',
            value_type='text',
            group_ids = [self.attribute_group_1.id],
            is_variation = 1
        )
        self.uom_ratio_attr = fake.attribute(
            code='uom_ratio',
            value_type='text',
            group_ids = [self.attribute_group_1.id],
            is_variation=1
        )

        self.material_attribute = fake.attribute(
            code='material',
            value_type='text',
            group_ids = [self.attribute_group_1.id],
            is_variation = 0
        )

        self.screen_attribute = fake.attribute(
            code='screen',
            value_type='text',
            group_ids = [self.attribute_group_1.id],
            is_variation = 1
        )

        self.attr_option_cai = fake.attribute_option(self.unit_attribute.id, value='Cái')
        self.attr_option_chiec = fake.attribute_option(self.unit_attribute.id, value='Chiếc')
        self.attr_option_thung = fake.attribute_option(self.unit_attribute.id, value='Thùng')
        self.attr_option_1 = fake.attribute_option(self.uom_ratio_attr.id, value='1')
        self.attr_option_10 = fake.attribute_option(self.uom_ratio_attr.id, value='10')

    def test_move_multiple_skus_to_single_product_return_200(self):
        # move cac san pham a sang aa ma co cung model
        skus = [self.iphone12_mini_blue.sku, self.thung_iphone12_mini_blue.sku]
        target_product_id = self.iphone_13.id
        code, body = self.call_api(data={
            "skus": skus,
            "sellerId": self.seller.id,
            "targetProductId": target_product_id
        })
        assert code == 200
        self.check_products_from_db(skus, target_product_id)

    def test_move_multiple_skus_to_single_product_different_base_uom_return_400(self):
        skus = [self.black_t_shirt.sku]
        code, body = self.call_api(data={
            "skus": skus,
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_13.id
        })
        assert code == 400
        message = body["message"]
        code_message = body["code"]
        assert "Khác đơn vị tính cơ sở:" in message
        assert code_message == 'INVALID'

    def test_move_single_sku_to_single_product_return_200(self):
        code, body = self.call_api(data={
            "skus": [self.thung_iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_13.id
        })
        assert code == 200
        self.check_products_from_db([self.thung_iphone12_mini_blue.sku], self.iphone_13.id)

    def test_move_sku_to_single_product_missing_sku_return_400(self):
        code, body = self.call_api(data={
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_13.id
        })
        assert code == 400
        assert body["code"] == "INVALID"
        assert body["message"] == "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại"
        assert body["result"][0]["field"] == "skus"
        assert body["result"][0]["message"][0] == "Missing data for required field."

    def test_move_sku_to_single_product_missing_sellerId_return_400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone13_mini_red.sku],
            "targetProductId": self.iphone_12.id
        })
        assert code == 400
        assert body["code"] == "INVALID"
        assert body["message"] == "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại"
        assert body["result"][0]["field"] == "sellerId"
        assert body["result"][0]["message"][0] == "Missing data for required field."

    def test_move_sku_to_single_product_missing_targetProductId_return_400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
        })
        assert code == 400
        assert body["code"] == "INVALID"
        assert body["message"] == "Nhập dữ liệu không hợp lệ, vui lòng kiểm tra lại"
        assert body["result"][0]["field"] == "targetProductId"
        assert body["result"][0]["message"][0] == "Missing data for required field."

    def test_move_sku_to_single_product_different_sellerId_return_400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone12_mini_blue.sku],
            "sellerId": self.get_max_seller_id() + 1,
            "targetProductId": self.iphone_13.id
        })
        assert code == 400
        assert body["code"] == "INVALID"
        assert body["message"] == "Danh sách sku có sản phẩm không tồn tại"

    def test_move_skus_to_single_different_model_return400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone13_mini_red.sku, self.iphone13_mini_green.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.cloth.id
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_single_sku_to_single_different_model_return400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone13_mini_green.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.cloth.id
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_single_sku_to_single_none_exist_product_return400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone13_mini_green.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.get_max_product_id() + 1
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_skus_to_single_none_exist_product_return400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone13_mini_green.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.get_max_product_id() + 1
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_skus_to_single_different_category_product_have_no_sellable_product_return400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_14.id
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_skus_to_single_different_category_but_same_attribute_set_product_return200(self):
        diff_category_product = models.Product.query.get(self.iphone_13.id)
        diff_category_product.category_id = self.mobile_category.id
        models.db.session.commit()

        code, body = self.call_api(data={
            "skus": [self.thung_iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": diff_category_product.id
        })
        assert code == 200
        self.check_products_from_db([self.thung_iphone12_mini_blue.sku], diff_category_product.id)

    def test_move_sku_to_product_have_no_sellable_product_return400(self):
        code, body = self.call_api(data={
            "skus": [self.thung_iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_14.id
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_sku_to_single_different_brand_product_have_a_sellable_product_return400(self):
        code, body = self.call_api(data={
            "skus": [self.iphone13_mini_red.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.cloth.id
        })
        assert code == 400
        assert body["code"] == "INVALID"

    def test_move_sku_with_more_attribute_than_target_product_return_200(self):
        self.add_attribute_to_product(product_id=self.iphone_12.id, attribute_id=self.material_attribute.id, value='iron')
        code, body = self.call_api(data={
            "skus": [self.thung_iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_13.id
        })
        assert code == 200
        self.check_products_from_db([self.thung_iphone12_mini_blue.sku], self.iphone_13.id)
    def test_move_sku_with_less_attribute_than_target_product_return_200(self):
        self.add_attribute_to_product(product_id=self.iphone_13.id, attribute_id=self.material_attribute.id, value='iron')
        code, body = self.call_api(data={
            "skus": [self.thung_iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_13.id
        })
        assert code == 200
        self.check_products_from_db([self.thung_iphone12_mini_blue.sku], self.iphone_13.id)

    def test_move_sku_with_less_variation_attribute_than_target_product_return_200(self):
        self.add_attribute_to_product(product_id=self.iphone_13.id, attribute_id=self.screen_attribute.id, value='FullHD')
        code, body = self.call_api(data={
            "skus": [self.thung_iphone12_mini_blue.sku],
            "sellerId": self.seller.id,
            "targetProductId": self.iphone_13.id
        })
        assert body['code'] == 'INVALID'
        assert body['message'] == f"SKU: {self.thung_iphone12_mini_blue.seller_sku} không di chuyển được vì các thuộc tính không phù hợp"


        