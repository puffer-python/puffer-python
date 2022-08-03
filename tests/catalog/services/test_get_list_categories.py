#coding=utf-8

from tests.catalog.api import APITestCase
from tests.faker import fake
from catalog.services.categories.category import CategoryService


service = CategoryService.get_instance()


class GetListCategoryTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-267'

    def setUp(self):
        self.seller = fake.seller()
        self.categories = list()
        self.master_category = fake.master_category()
        for _ in range(12):
            self.categories.append(fake.category(seller_id=self.seller.id,
                                                 master_category_id=self.master_category.id))
        self.categories.append(fake.category(
            parent_id=self.categories[0].id,
            seller_id=self.seller.id
        ))
        self.other_category = fake.category(seller_id=fake.seller().id)

    def test_passPageSizeSmallLessTotalRecords__returnPageSizeRecordsCategory(self):
        page_size = 10
        page = 1
        categories, total_records = service.get_list_categories({
            'seller_id': self.seller.id
        }, page=page, page_size=page_size, seller_id=self.seller.id)
        assert total_records == len(self.categories)
        assert len(categories) == 10

    def test_passPageOne__returnRemainRecordsCategory(self):
        page_size = 10
        page = 2

        categories, total_records = service.get_list_categories({
            'seller_id': self.seller.id
        }, page=page, page_size=page_size, seller_id=self.seller.id)
        assert total_records == len(self.categories)
        assert len(categories) == 3

    def test_passLevel2__returnListHaveOneElem(self):
        level = 2
        page = 0
        page_size = 10

        categories, total_records = service.get_list_categories({
            'seller_id': self.seller.id,
            'depth': level
        }, page=page, page_size=page_size)
        assert total_records == 1
        assert len(categories) == 1

    def test_passFilters__returnListCategories(self):
        page = 0
        page_size = 13

        categories, total_records = service.get_list_categories({
            'seller_id': self.seller.id,
            'is_active': True
        }, page=page, page_size=page_size, seller_id=self.seller.id)
        real_active_categories = list(filter(lambda item: item.is_active, self.categories))
        assert len(categories) == len(real_active_categories)
        assert total_records == len(real_active_categories)

    def test_passIdsFilter__returnListCategories(self):
        ids = f'{self.categories[0].id},{self.categories[1].id},{self.categories[2].id}'
        categories, total_records = service.get_list_categories({
            'ids': ids
        }, page=0, page_size=10, seller_id=self.seller.id)
        assert len(categories) == 3
        for a, b in zip(categories, self.categories[:3]):
            assert a.id == b.id
            assert a.master_category_id == self.master_category.id
