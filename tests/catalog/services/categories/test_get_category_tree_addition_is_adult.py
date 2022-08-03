#coding=utf-8

from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user

class GetCategoryTreeTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1536'
    FOLDER = '/Category/GetCategoryTreeTestCase'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.n_sale_category_is_result = 0
        self.parent_category = fake.category(is_active=True, parent_id=0, seller_id=self.seller.id, is_adult=False)
        self.categories_active = []
        self.category_not_children = fake.category(is_active=True, parent_id=0, seller_id=self.seller.id, is_adult=True)
        self.categories_inactive = [fake.category(is_active=False, parent_id=0, seller_id=self.seller.id, is_adult=False)]
        for _ in range(5):
            category = fake.category(
                is_active=fake.random_element((True, False)),
                parent_id= self.parent_category.id,
                seller_id=self.seller.id,
            )
            if category.is_active and category.parent.is_active:
                self.n_sale_category_is_result += 1
                self.categories_active.append(category)
        self.categories_inactive.append(fake.category(
            is_active=False,
            parent_id=self.categories_inactive[0].id,
            seller_id=self.seller.id,
            is_adult=True
        ))

    def url(self, category_id):
        return '/categories/{}/children'.format(category_id)

    def method(self):
        return 'GET'

    def get_method(self, category_id):
        with logged_in_user(self.user):
            return self.call_api(url=self.url(category_id))

    def assert_category(self, category_object, category_result):
        children = category_result.get('children', None)
        assert category_object.id == category_result['id']
        assert category_object.name == category_result['name']
        assert category_object.code == category_result['code']
        assert category_object.is_adult == category_result['isAdult']
        assert bool(category_object.get_children({'is_active': True})) == bool(children)
        if children is not None:
            list_cate_json = sorted(
                children,
                key=lambda cate: cate['id']
            )
            list_cate_obj = sorted(
                category_object.get_children({'is_active': True}),
                key=lambda cate: cate.id
            )
            for cate_obj, cate_result in zip(list_cate_obj, list_cate_json):
                self.assert_category(cate_obj, cate_result)

    def test_get_categories_tree_with_is_adult_return_200(self):
        category_id = self.parent_category.id
        code, body = self.get_method(category_id=category_id)
        category_result = body['result']
        assert code == 200
        self.assert_category(self.parent_category, category_result)

    def test_get_categories_tree_with_is_adult_on_leaf_no_child_return_200(self):
        category_id = self.categories_active[0].id
        code, body = self.get_method(category_id=category_id)
        category_result = body['result']
        assert code == 200
        assert category_result.get('children', None) is None
        self.assert_category(self.categories_active[0], category_result)

    def test_get_categories_tree_return_400_when_category_inactive(self):
        category_id = self.categories_inactive[0].id
        code, body = self.get_method(category_id=category_id)
        assert code == 400
        assert body['code'] == 'INVALID'
        assert body['message'] == 'Danh mục đang vô hiệu'

class GetCategoryListTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-1533'
    FOLDER = '/Category/GetCategories/AdditionIsAdult'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)

        self.platform = fake.platform_sellers(platform_id=1, seller_id=self.seller.id, is_default=True,
                              is_owner=True)

        self.n_sale_category_is_result = 0
        self.categories = []
        self.categories_id = []
        self.parent_category = fake.category(is_active=True, parent_id=0, seller_id=self.seller.id, is_adult=False)
        self.categories_id.append(self.parent_category.id)
        self.categories.append(self.parent_category)
        self.category_not_children = fake.category(is_active=True, parent_id=0, seller_id=self.seller.id, is_adult=True)
        self.categories_id.append(self.category_not_children.id)
        self.categories.append(self.category_not_children)
        categories_inactive = fake.category(is_active=False, parent_id=0, seller_id=self.seller.id, is_adult=False)
        self.categories_id.append(categories_inactive.id)
        self.categories.append(categories_inactive)
        for _ in range(5):
            category = fake.category(
                is_active=fake.random_element((True, False)),
                parent_id= self.parent_category.id,
                seller_id=self.seller.id,
            )
            self.categories_id.append(category.id)
            self.categories.append(category)

    def url(self):
        return '/categories'

    def method(self):
        return 'GET'

    def get_method(self, **kwargs):
        with logged_in_user(self.user):
            url = f'{self.url()}?page={kwargs.get("page", 1)}&pageSize={kwargs.get("pageSize", 10)}'
            for key, value in kwargs.items():
                if key not in ("page", "pageSize"):
                    url += f'&{key}={value}'
            print(url)
            return self.call_api(url=url)

    def assert_category(self, categories_object, categories_result):
        for category_object, category_result in zip(categories_object, categories_result):
            assert category_object.id == category_result['id']
            assert category_object.name == category_result['name']
            assert category_object.code == category_result['code']
            assert category_result.get('isAdult', None) is not None
            assert category_object.is_adult == category_result['isAdult']
        
    def test_get_list_categories_return_with_is_adult_response_code_200(self):
        code, body = self.get_method()
        categories_result = body['result']['categories']
        print(self.categories)
        assert code == 200
        self.assert_category(self.categories, categories_result)

    def test_get_list_2_categories_return_with_is_adult_response_code_200(self):
        ids = f'{self.categories_id[0]},{self.categories_id[1]}'
        code, body = self.get_method(
            ids=ids
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = filter(lambda category: category.id in [self.categories_id[0],self.categories_id[1]], self.categories)

        assert code == 200
        assert total_record == 2
        self.assert_category(sample_categories_from_db, categories)
    def test_get_list_1_categories_return_with_is_adult_response_code_200(self):
        ids = f'{self.categories_id[0]}'
        code, body = self.get_method(
            ids=ids
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = filter(lambda category: category.id == self.categories_id[0], self.categories)

        assert code == 200
        assert total_record == 1
        self.assert_category(sample_categories_from_db, categories)
    def test_get_list_1_when_id_not_exist_categories_return_with_is_adult_response_code_200(self):
        ids = f'{self.categories_id[0]},-9'
        code, body = self.get_method(
            ids=ids
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = filter(lambda category: category.id in [-9, self.categories_id[0]], self.categories)

        assert code == 200
        assert total_record == 1
        self.assert_category(sample_categories_from_db, categories)
    def test_get_list_active_categories_return_with_is_adult_response_code_200(self):
        code, body = self.get_method(
            isActive=True
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = list(filter(lambda category: category.is_active == True, self.categories))
        assert code == 200
        assert total_record == len(sample_categories_from_db)
        self.assert_category(sample_categories_from_db, categories)

    def test_get_list_inactive_categories_return_with_is_adult_response_code_200(self):
        code, body = self.get_method(
            isActive=False
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = list(filter(lambda category: category.is_active == False, self.categories))
        assert code == 200
        assert total_record == len(sample_categories_from_db)
        self.assert_category(sample_categories_from_db, categories)

    def test_get_list_with_level_categories_return_with_is_adult_response_code_200(self):
        level = self.categories[1].depth
        code, body = self.get_method(
            level=level
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = list(filter(lambda category: category.depth == level, self.categories))
        assert code == 200
        assert total_record == len(sample_categories_from_db)
        self.assert_category(sample_categories_from_db, categories)

    def test_get_list_1_when_code_not_exist_categories_return_with_is_adult_response_code_200(self):
        codes = f'{self.categories[0].code},-9'
        code, body = self.get_method(
            codes=codes
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = filter(lambda category: category.code in [-9, self.categories[0].code], self.categories)

        assert code == 200
        assert total_record == 1
        self.assert_category(sample_categories_from_db, categories)

    def test_get_list_with_multiple_codes_categories_return_with_is_adult_response_code_200(self):
        platform_Id = self.platform.platform_id
        code, body = self.get_method(
            platformId=platform_Id
        )
        result = body['result']
        total_record = result['totalRecords']
        assert code == 200
        assert total_record == len(self.categories)

    def test_get_list_categories_with_platformId_return_with_is_adult_response_code_200(self):
        codes = f'{self.categories[0].code},{self.categories[1].code}'
        code, body = self.get_method(
            codes=codes
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = filter(lambda category: category.code in [self.categories[0].code,self.categories[1].code], self.categories)

        assert code == 200
        assert total_record == len(list(sample_categories_from_db))
        self.assert_category(sample_categories_from_db, categories)

    def test_get_list_categories_with_query_return_with_is_adult_response_code_200(self):
        query = f'{self.categories[0].name}'
        code, body = self.get_method(
            query=query
        )
        result = body['result']
        categories = result['categories']
        total_record = result['totalRecords']
        sample_categories_from_db = filter(lambda category: category.name == self.categories[0].name, self.categories)

        assert code == 200
        assert total_record == len(list(sample_categories_from_db))
        self.assert_category(sample_categories_from_db, categories)
