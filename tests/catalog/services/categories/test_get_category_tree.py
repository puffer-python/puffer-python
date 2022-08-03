#coding=utf-8


from catalog import models as m
from catalog.services.categories import CategoryService
from tests.catalog.api import APITestCase
from tests.faker import fake


service = CategoryService.get_instance()


class GetCategoryTreeTestCase(APITestCase):
    ISSUE_KEY = 'SC-395'

    def setUp(self):
        self.seller = fake.seller()
        self.user = fake.iam_user(seller_id=self.seller.id)
        self.n_sale_category_is_result = 0
        self.categories_active = [fake.category(is_active=True, parent_id=0, seller_id=self.seller.id)]
        self.category_not_children = fake.category(is_active=True, parent_id=0, seller_id=self.seller.id)
        self.categories_inactive = [fake.category(is_active=False, parent_id=0, seller_id=self.seller.id)]
        for _ in range(5):
            category = fake.category(
                is_active=fake.random_element((True, False)),
                parent_id=fake.random_element(self.categories_active).id,
                seller_id=self.seller.id,
            )
            if category.is_active and category.parent.is_active:
                self.n_sale_category_is_result += 1
            self.categories_active.append(category)
        self.categories_inactive.append(fake.category(
            is_active=True,
            parent_id=self.categories_inactive[0].id,
            seller_id=self.seller.id,
        ))

    def assertCategory(self, category_object, category_result):
        children = getattr(category_result, '_children', None)
        assert category_object.id == category_result.id
        assert category_object.name == category_result.name
        assert category_object.code == category_result.code
        assert bool(category_object.get_children({'is_active': True})) == bool(children)
        if children is not None:
            list_cate_json = sorted(
                children,
                key=lambda cate: cate.id
            )
            list_cate_obj = sorted(
                category_object.get_children({'is_active': True}),
                key=lambda cate: cate.id
            )
            for cate_obj, cate_result in zip(list_cate_obj, list_cate_json):
                self.assertCategory(cate_obj, cate_result)

    def test_passCategoryWithAllChildrenInactive__returnOneChild(self):
        for i in range(1, len(self.categories_active)):
            self.categories_active[i].is_active = False
        m.db.session.commit()

        ret = service.get_category_tree(self.categories_active[0].id,
                                        self.seller.id)
        self.assertCategory(
            self.categories_active[0],
            ret
        )

    def test_passLeafCategory__returnOneCategory(self):
        ret = service.get_category_tree(self.category_not_children.id,
                                        self.seller.id)
        self.assertCategory(
            self.category_not_children,
            ret
        )

    def test_passCategoryHasManyChildren__returnTreeCategory(self):
        ret = service.get_category_tree(self.categories_active[0].id,
                                        self.seller.id)
        self.assertCategory(
            self.categories_active[0],
            ret
        )
