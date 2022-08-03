from tests.catalog.api import APITestCase
from tests.faker import fake
from tests import logged_in_user


class GetImportHistoryByIdTestCase(APITestCase):
    ISSUE_KEY = 'CATALOGUE-363'
    FOLDER = '/Import/Histories/GetById'

    def url(self):
        return '/import/histories/{}'.format(self.his_id)

    def method(self):
        return 'GET'

    def setUp(self):
        self.user = fake.iam_user()
        records = [fake.file_import(user_info=self.user) for _ in range(3)]
        self.his = fake.random_element(records)
        self.his_id = self.his.id

    def testWithIdNotExist_return400(self):
        self.setUp()
        self.his_id = self.his.id + fake.id()
        with logged_in_user(self.user):
            code, _ = self.call_api()

        assert code == 400

    def test_withIdValid_return200(self):
        self.setUp()
        with logged_in_user(self.user):
            code, body = self.call_api()

        assert code == 200

    def testCheckTotalPage_return200(self):
        self.setUp()
        with logged_in_user(self.user):
            code, body = self.call_api(self.url())

        assert code == 200
        assert self.his.total_row == body['result']['totalRow']

    def testCheckStatus_return200(self):
        self.setUp()
        with logged_in_user(self.user):
            code, body = self.call_api(self.url())
        assert self.his.status == body['result']['status']

    def testPath_return200(self):
        self.setUp()
        with logged_in_user(self.user):
            code, body = self.call_api(self.url())
        assert self.his.path == body['result']['path']

    def testSuccessPath_return200(self):
        self.setUp()
        with logged_in_user(self.user):
            code, body = self.call_api(self.url())
        assert self.his.success_path == body['result']['successPath']

    def testCreatedBy_return200(self):
        """
        Check Created By 
        """
        self.setUp()
        with logged_in_user(self.user):
            code, body = self.call_api(self.url())
        assert self.his.created_by == body['result']['createdBy']

    def testIdInvalidSeller_return400(self):
        """
        Test API with anther seller
        """
        self.setUp()
        new_user = fake.iam_user(seller_id=self.user.seller_id + fake.id())
        fake_his = fake.file_import(user_info=self.user)
        self.his_id = fake_his.id + fake.id()
        with logged_in_user(new_user):
            code, body = self.call_api()
        assert code == 400
