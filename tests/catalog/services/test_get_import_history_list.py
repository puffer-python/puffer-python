#coding=utf-8

from datetime import datetime

from catalog.services.imports import FileImportService
from tests.catalog.api import APITestCase
from tests.faker import fake


TIME_FMT = '%d/%m/%Y'


service = FileImportService.get_instance()

class GetImportHistoryListTestCase(APITestCase):
    ISSUE_KEY = 'SC-459'

    def setUp(self):
        self.user = fake.iam_user()
        self.n_records = 5
        self.records = [fake.file_import(user_info=self.user) for _ in range(self.n_records)]
        self.data = dict(
            filters={},
            sort_order=None,
            sort_field=None,
            page=1,
            page_size=10,
            seller_id=self.user.seller_id
        )

    def assertFileImport(self, list1, list2):
        assert len(list1) == len(list2)
        for a, b in zip(sorted(list1, key=lambda x: x.id), sorted(list2, key=lambda x: x.id)):
            assert a == b

    def test_passValidData__allowPass(self):
        res, _ = service.get_import_histories(**self.data)
        self.assertFileImport(res, self.records)

    def test_withDataHaveRecordOwnedByOtherSeller__returnRecordOwnerBySelf(self):
        other_user = fake.iam_user(self.user.seller_id + 1)
        fake.file_import(user_info=other_user)
        res, _ = service.get_import_histories(**self.data)
        self.assertFileImport(res, self.records)

    def test_withStatusFilter__returnValidRecords(self):
        status = fake.random_elements(('new', 'processing', 'success'))
        self.data['filters']['status'] = status
        true_list = list(filter(lambda x: x.status in status, self.records))
        res, _ = service.get_import_histories(**self.data)
        self.assertFileImport(res, true_list)

    def test_withTypeFilter__returnValidRecords(self):
        types = fake.random_elements(('create_product', 'update_product'))
        self.data['filters']['type'] = types
        true_list = list(filter(lambda x: x.type in types, self.records))
        res, _ = service.get_import_histories(**self.data)
        self.assertFileImport(res, true_list)

    def test_withDateRangeFilter__returnValidRecords(self):
        self.data['filters'] = {
            'start_at': datetime.strptime('1/1/1970', TIME_FMT),
            'end_at': datetime.strptime('2/1/1970', TIME_FMT)
        }
        a = fake.file_import(created_at=datetime.fromtimestamp(0), user_info=self.user)
        res, _ = service.get_import_histories(**self.data)
        self.assertFileImport(res, [a])
