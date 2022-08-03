# coding=utf-8
import logging
import os

import pytest
import requests

import config

from datetime import datetime
from operator import itemgetter

__author__ = 'Kien'

_logger = logging.getLogger(__name__)

TEST_DIR = os.path.join(config.ROOT_DIR, 'tests')

config.CACHE_TYPE = 'simple'
config.TESTING = True

config.CELERY_BROKER_URL = 'memory://'
config.CELERY_RESULT_BACKEND = 'db+sqlite://'
config.BROKER_URL = 'memory://'


@pytest.fixture(scope='session')
def app(request):
    from catalog import create_app

    config.DEBUG = False
    app = create_app()
    from catalog.extensions import flask_cache
    flask_cache.init_cache(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['MEDIA_IMPORT_DIR'] = os.path.join(config.ROOT_DIR, 'media', 'import', 'tests')

    return app


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, 'test_outcome', rep)


def pytest_addoption(parser):
    parser.addoption(
        '--submit-tests',
        action='store_true',
        help='Submit tests to Jira')
    parser.addoption(
        '--process',
        action='store',
        default='0',
        help='the order of the process')
    parser.addoption(
        '--total-processes',
        action='store',
        default='1',
        help='the total processes')


class JiraTestService():
    _TEST_CASE = 'TEST_CASE'
    _TEST_CYCLE = 'TEST_RUN'

    def __init__(self, jira_settings):
        self.project_key = jira_settings['project_key']
        self.auth_string = (jira_settings['user'], jira_settings['password'])
        self.url = jira_settings['url'] + '/rest/atm/1.0'
        self.issue_url = jira_settings['url'] + '/rest/api/latest/issue'
        self.folder = jira_settings['folder']

    def get_issue_info(self, issue_key):
        return requests.get(url=self.issue_url + '/' + issue_key,
                            auth=self.auth_string).json()

    def get_tests_in_issue(self, issue_key):
        params = {
            'query':
                'projectKey = "%s" AND issueKeys IN (%s)' %
                (self.project_key, issue_key)
        }
        response = requests.get(url=self.url + '/testcase/search',
                                params=params,
                                auth=self.auth_string).json()
        print(response)
        return list(map(itemgetter('name', 'key'), response))

    def create_folder(self, name: str, type: str = _TEST_CASE):
        folder = self.folder + f'{name}'

        data = {
            "projectKey": self.project_key,
            "name": folder,
            "type": type
        }

        url = self.url + "/folder"

        res = requests.post(url=url, json=data, auth=self.auth_string)

        if res.status_code == 401:
            raise Exception(f"Unauthorized: Authenticated failed.")

        if res.status_code == 403:
            raise Exception(f"Forbidden: You don't have permission to send request POST to {url} with payload {data}.")

        return folder

    def create_test(self, test_name, issue_key, folder):
        folder = self.create_folder(folder)

        json = {
            'name': test_name,
            'projectKey': self.project_key,
            'issueLinks': [issue_key],
            "labels": [issue_key],
            'status': 'Draft',
            'folder': folder
        }
        response = requests.post(url=self.url + '/testcase',
                                 json=json,
                                 auth=self.auth_string)
        if response.status_code != 201:
            raise Exception('Create test return with error status code',
                            response.status_code)

        test_key = response.json()['key']
        return test_key

    def delete_test(self, test_key):
        response = requests.delete(url=self.url + '/testcase/' + test_key,
                                   auth=self.auth_string)
        if response.status_code != 204:
            raise Exception('Delete test return with error status code',
                            response.status_code)

    def create_test_cycle(self, name, issue_key, items, folder):
        def get_current_time():
            return datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        folder = self.create_folder(name=folder, type=self._TEST_CYCLE)

        json = {
            'name': name,
            'projectKey': self.project_key,
            'issueKey': issue_key,
            'plannedStartDate': get_current_time(),
            'plannedEndDate': get_current_time(),
            'items': items,
            'folder': folder
        }
        response = requests.post(url=self.url + '/testrun',
                                 json=json,
                                 auth=self.auth_string)
        if response.status_code != 201:
            raise Exception('Create test cycle return with error status code',
                            response.status_code)


def jira_test_service():
    return JiraTestService({
        'url': 'https://jira.teko.vn',
        'user': 'dung.bv',
        'password': '123456a@',
        'project_key': 'CATALOGUE',
        'folder': '/HN1/API'
    })


delete_tests_on_issue = set()


@pytest.fixture(scope='class')
def each_test_suite(request):
    # Before each test suite
    cls = request.cls
    cls.results = {}
    cls.tests_list = []

    test_service = jira_test_service()  # Currently only support Jira

    submit_tests = request.config.getoption('--submit-tests', default=False)
    if not getattr(cls, 'ISSUE_KEY', None) or not submit_tests:
        submit_tests = False
    else:
        issue_info = test_service.get_issue_info(cls.ISSUE_KEY)
        if issue_info['fields']['status']['name'] == 'Closed':
            submit_tests = False

    if submit_tests:
        cls.tests_list = test_service.get_tests_in_issue(cls.ISSUE_KEY)

        if cls.ISSUE_KEY not in delete_tests_on_issue:
            for _, test_key in cls.tests_list:
                test_service.delete_test(test_key)
            delete_tests_on_issue.add(cls.ISSUE_KEY)

    yield

    # After each test suite
    if submit_tests:
        # Create test keys
        for name in cls.results:
            test_key = test_service.create_test(
                test_name=cls.__name__ + '_' + name,
                issue_key=cls.ISSUE_KEY,
                folder=getattr(cls, 'FOLDER', '')
            )
            cls.results[name]['testCaseKey'] = test_key
        test_cycle_items = [v for k, v in cls.results.items()]

        # Create test cycle
        test_service.create_test_cycle(
            name=cls.ISSUE_KEY + ' - ' + cls.__name__,
            issue_key=cls.ISSUE_KEY,
            items=test_cycle_items,
            folder=getattr(cls, 'FOLDER', '')
        )


@pytest.fixture()
def each_test_case(request):
    # Before each test case
    MAX_NAME_LENGTH = 255
    name = request._pyfuncitem.name
    if len(name) > MAX_NAME_LENGTH:
        name = name.substring(0, MAX_NAME_LENGTH)
    request.cls.results[name] = {'status': 'Pass'}
    yield

    # After each test case
    if request.node.test_outcome.failed:
        request.cls.results[name]['status'] = 'Fail'
