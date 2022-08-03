from catalog.services.imports.template_base import TemplateBase
from tests import logged_in_user
from tests.catalog.api import APITestCase
from tests.faker import fake


class GenerateCategoryTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-416'
    FOLDER = '/CreateProductTemplate/Generate'

    def fake_categories(self, catagory_status_list=[1, 1, 1]):
        self.categories_level_0 = fake.category(
            is_active=catagory_status_list[0], parent_id=0,
            seller_id=self.seller.id
        )
        self.categories_level_1 = fake.category(
            is_active=catagory_status_list[1], parent_id=self.categories_level_0.id,
            seller_id=self.seller.id
        )
        self.categories_level_2 = fake.category(
            is_active=catagory_status_list[2], parent_id=self.categories_level_1.id,
            seller_id=self.seller.id
        )

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.service = TemplateBase(import_type='create_product')

    def test_loadCategory(self):
        self.fake_categories(catagory_status_list=[1, 1, 1])

        with logged_in_user(self.user):
            categories = self.service._load_category_data(title=None)

            self.assertEqual(len(categories), 1)
            self.assertEqual(categories[0].id, self.categories_level_2.id)

    def test_loadLevel1Category_withAllLevel2ChildInactive(self):
        self.fake_categories(catagory_status_list=[1, 1, 0])

        with logged_in_user(self.user):
            categories = self.service._load_category_data(title=None)

            self.assertEqual(len(categories), 1)
            self.assertEqual(categories[0].id, self.categories_level_1.id)

    def test_loadLevel1Category_withNotAllChildInActive(self):
        self.fake_categories(catagory_status_list=[1, 1, 1])
        self.categories_level_2_2 = fake.category(
            is_active=0,
            parent_id=self.categories_level_1.id,
            seller_id=self.seller.id
        )

        with logged_in_user(self.user):
            categories = self.service._load_category_data(title=None)

            self.assertEqual(len(categories), 1)
            self.assertEqual(categories[0].id, self.categories_level_2.id)

    def test_loadRootCategory_withAllTreeInActive(self):
        self.fake_categories(catagory_status_list=[0, 0, 0])
        self.categories_level_2_2 = fake.category(
            is_active=0,
            parent_id=self.categories_level_1.id,
            seller_id=self.seller.id
        )

        with logged_in_user(self.user):
            categories = self.service._load_category_data(title=None)

            self.assertEqual(len(categories), 0)


