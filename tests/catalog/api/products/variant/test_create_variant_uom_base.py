# coding=utf-8
from mock import patch

from catalog import models
from tests.catalog.api import APITestCase
from tests.faker import fake


class CreateVariantWithUomBaseAPITestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-592'
    FOLDER = '/Variants/Create/UomBase/Validation'

    def url(self):
        return '/variants'

    def method(self):
        return 'POST'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.attribute_set = fake.attribute_set()
        self.group = fake.attribute_group(self.attribute_set.id)
        self.attribute_uom = fake.attribute(code='uom', value_type='selection')
        self.attribute_ratio = fake.attribute(code='uom_ratio', value_type='text')
        self.attributes = [fake.attribute(value_type='selection') for _ in range(10)]
        self.attributes.append(self.attribute_uom)
        self.options = [fake.attribute_option(attribute.id) for attribute in self.attributes]
        self.attributes.append(self.attribute_ratio)
        self.attribute_group_attribute = [fake.attribute_group_attribute(
            attribute_id=attr.id,
            group_ids=[self.group.id],
            is_variation=True
        ) for attr in self.attributes]
        self.master_category = fake.master_category(
            is_active=True
        )
        self.category = fake.category(
            seller_id=self.user.seller_id,
            is_active=True,
        )
        self.product = fake.product(
            master_category_id=self.master_category.id,
            category_id=self.category.id,
            attribute_set_id=self.attribute_set.id,
            created_by=self.user.email
        )
        self.product_category = fake.product_category(
            product_id=self.product.id,
            category_id=self.category.id
        )

        self.patcher_seller = patch('catalog.services.seller.get_seller_by_id')
        self.mock_seller = self.patcher_seller.start()

    def tearDown(self):
        self.patcher_seller.stop()

    def __add_uom_ratio_variant(self, value=1.0):
        fake.product_variant_attribute(product_variant_id=self.variant.id,
                                       attribute_id=self.attribute_ratio.id, value=value)

    def __init_ratio_value(self, value):
        return {
            'id': self.attribute_ratio.id,
            'value': value
        }

    def __init_variant_attribute_values(self):
        attributes = list()
        for attr in self.attribute_group_attribute:
            if attr.attribute_id == self.attribute_ratio.id:
                continue
            attributes.append({
                'id': attr.attribute_id,
                'value': fake.random_element(attr.attribute.options).id
            })
        self.variant_attribute_values = attributes

    def __add_not_variant_attribute(self):
        attribute = fake.attribute(value_type='text')
        fake.attribute_group_attribute(
            attribute_id=attribute.id,
            group_ids=[self.group.id],
            is_variation=False
        )
        fake.product_variant_attribute(product_variant_id=self.variant.id, attribute_id=attribute.id, value='')

    def __add_default_variant_attribute_values(self, diff_attribute_id=None):
        self.variant = fake.product_variant_only(product_id=self.product.id)
        for va in self.variant_attribute_values:
            value = va['value']
            if diff_attribute_id:
                new_option = fake.attribute_option(diff_attribute_id)
                value = new_option.id
            fake.product_variant_attribute(product_variant_id=self.variant.id, attribute_id=va['id'], value=value)
        self.__add_not_variant_attribute()
        models.db.session.commit()

    def __init_default_variant_attribute_values_with_ratio(self, diff_attribute_id=None, ratio_value=1.0):
        self.__init_variant_attribute_values()
        self.__add_default_variant_attribute_values(diff_attribute_id)
        self.__add_uom_ratio_variant(value=ratio_value)

    def __init_attributes(self, value_ratio):
        attributes = [self.__init_ratio_value(value_ratio)]
        attributes.extend(self.variant_attribute_values)
        return attributes

    def __init_request_multi_variants(self, values_ratio, diff_unit=False):
        variants = []
        for value_ratio in values_ratio:
            attributes = self.__init_attributes(value_ratio)
            if diff_unit:
                new_attributes = []
                option = fake.attribute_option(self.attribute_uom.id)
                for attr in attributes:
                    item = {
                        'id': attr['id'],
                        'value': attr['value']
                    }
                    if attr['id'] == self.attribute_uom.id:
                        item['value'] = option.id
                    new_attributes.append(item)
            else:
                new_attributes = attributes
            variants.append({
                'attributes': new_attributes
            })
        data = {
            'productId': self.product.id,
            'variants': variants
        }
        return self.call_api_with_login(data=data)

    def __get_variant_attribute(self):
        return models.VariantAttribute.query.filter(
            models.VariantAttribute.variant_id == self.variant.id,
            models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()

    def __get_variant(self, id):
        return models.ProductVariant.query.get(id)

    def test_create_variants_return400_with_no_uom_base(self):
        self.__init_variant_attribute_values()
        code, response = self.__init_request_multi_variants([0.8])
        self.assertEqual(400, code)
        self.assertEqual('Vui lòng nhập thông tin đơn vị tính cơ sở', response['message'])

    def test_create_variants_return400_add_new_uom_base_when_exists_another_uom_base(self):
        self.__init_default_variant_attribute_values_with_ratio()
        code, response = self.__init_request_multi_variants([1.0])
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể có đơn vị tính cơ sở với ratio=1', response['message'])

    def test_create_variants_return400_add_new_uom_base_when_duplicated_uom_base_input(self):
        self.__init_variant_attribute_values()
        code, response = self.__init_request_multi_variants([1.0, 1.0], diff_unit=True)
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể có đơn vị tính cơ sở với ratio=1', response['message'])

    def test_create_variants_return400_when_only_one_base_uom_and_many_ratioes_not_equal_1_input(self):
        self.__init_variant_attribute_values()
        code, response = self.__init_request_multi_variants([1.0, 2.0, 0.5])
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể cùng loại có cùng đơn vị tính', response['message'])

    def test_create_variants_return400_with_uom_base_and_exists_other_ratio_not_equal_1(self):
        self.__init_default_variant_attribute_values_with_ratio()
        self.__add_default_variant_attribute_values()
        self.__add_uom_ratio_variant(value=0.9)

        code, response = self.__init_request_multi_variants([0.8])
        self.assertEqual(400, code)
        self.assertEqual('Đã tồn tại biến thể cùng loại có cùng đơn vị tính', response['message'])

    def test_create_variants_return200_add_new_uom_base_with_exists_uom_base_in_other_variants(self):
        self.__init_default_variant_attribute_values_with_ratio()
        self.__init_default_variant_attribute_values_with_ratio(diff_attribute_id=self.attributes[0].id)
        self.__add_uom_ratio_variant()

        code, response = self.__init_request_multi_variants([1.0])
        ratio_variant = self.__get_variant_attribute()
        variant = self.__get_variant(response['result']['variants'][0]['id'])

        self.assertEqual(200, code)
        self.assertEqual(1.0, float(ratio_variant.value))
        self.assertEqual(f'{variant.id}:{float(ratio_variant.value)},', variant.all_uom_ratios)

    def test_create_variants_return200_add_new_uom_base_with_not_exists_uom_base_in_this_variant(self):
        self.__init_variant_attribute_values()
        code, _ = self.__init_request_multi_variants([1.0])
        variant = models.ProductVariant.query.filter(models.ProductVariant.product_id == self.product.id).first()
        ratio_variant = models.VariantAttribute.query.filter(
            models.VariantAttribute.variant_id == variant.id,
            models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        self.assertEqual(200, code)
        self.assertEqual(1.0, float(ratio_variant.value))

    def test_create_variants_return200_with_uom_base_and_not_exists_any_ratio_not_equal_1(self):
        self.__init_default_variant_attribute_values_with_ratio()

        code, response = self.__init_request_multi_variants([0.5])
        ratio_variant = self.__get_variant_attribute()
        new_variant_id = response['result']['variants'][0]['id']
        new_ratio_variant = models.VariantAttribute.query.filter(models.VariantAttribute.variant_id == new_variant_id,
                                                                 models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        variant = self.__get_variant(new_variant_id)

        self.assertEqual(200, code)
        self.assertEqual(1.0, float(ratio_variant.value))
        self.assertEqual(0.5, float(new_ratio_variant.value))
        self.assertEqual(
            f'{ratio_variant.variant_id}:{float(ratio_variant.value)},{variant.id}:{float(new_ratio_variant.value)},', variant.all_uom_ratios)

    def test_create_variants_return200_when_only_one_base_uom_and_ratio_not_equal_1_input(self):
        self.__init_variant_attribute_values()
        code, response = self.__init_request_multi_variants([1.0, 0.5])
        new_variant_id1 = response['result']['variants'][0]['id']
        new_ratio_variant1 = models.VariantAttribute.query.filter(models.VariantAttribute.variant_id == new_variant_id1,
                                                                  models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        new_variant_id2 = response['result']['variants'][1]['id']
        new_ratio_variant2 = models.VariantAttribute.query.filter(models.VariantAttribute.variant_id == new_variant_id2,
                                                                  models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        self.assertEqual(200, code)
        self.assertEqual(1.0, float(new_ratio_variant1.value))
        self.assertEqual(0.5, float(new_ratio_variant2.value))

    def test_create_variants_return200_when_only_one_base_uom_and_many_ratioes_not_equal_1_in_diff_units_input(self):
        self.__init_variant_attribute_values()
        code, response = self.__init_request_multi_variants([1.0, 0.5, 2.0], diff_unit=True)
        new_variant_id1 = response['result']['variants'][0]['id']
        new_ratio_variant1 = models.VariantAttribute.query.filter(models.VariantAttribute.variant_id == new_variant_id1,
                                                                  models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        variant1 = self.__get_variant(new_variant_id1)

        new_variant_id2 = response['result']['variants'][1]['id']
        new_ratio_variant2 = models.VariantAttribute.query.filter(models.VariantAttribute.variant_id == new_variant_id2,
                                                                  models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        variant2 = self.__get_variant(new_variant_id2)

        new_variant_id3 = response['result']['variants'][2]['id']
        new_ratio_variant3 = models.VariantAttribute.query.filter(models.VariantAttribute.variant_id == new_variant_id3,
                                                                  models.VariantAttribute.attribute_id == self.attribute_ratio.id).first()
        variant3 = self.__get_variant(new_variant_id3)

        all_uom_ratios = f'{variant1.id}:{float(new_ratio_variant1.value)},{variant2.id}:{float(new_ratio_variant2.value)},{variant3.id}:{float(new_ratio_variant3.value)},'

        self.assertEqual(200, code)
        self.assertEqual(1.0, float(new_ratio_variant1.value))
        self.assertEqual(0.5, float(new_ratio_variant2.value))
        self.assertEqual(2.0, float(new_ratio_variant3.value))

        self.assertEqual(all_uom_ratios, variant1.all_uom_ratios)
        self.assertEqual(all_uom_ratios, variant2.all_uom_ratios)
        self.assertEqual(all_uom_ratios, variant3.all_uom_ratios)
