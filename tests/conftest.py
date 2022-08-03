# coding=utf-8
import os
import logging
import pytest
import flask_login
from unittest import mock

from sqlalchemy import MetaData, ForeignKeyConstraint, Table
from sqlalchemy.engine import reflection
from sqlalchemy.sql.ddl import DropConstraint

import config
from catalog.extensions import login_manager

__author__ = 'Kien'
_logger = logging.getLogger(__name__)


@pytest.fixture(scope='session')
def db(app, request):
    """Init database when run tests and drop all when finish"""

    from catalog import models

    def teardown():
        models.db.drop_all()

    models.db.app = app
    models.db.drop_all()
    models.db.create_all()

    request.addfinalizer(teardown)
    return models.db


def init_session(app, db, request):
    """Creates a new database session for a test."""
    if 'session_class' in request.keywords:
        return
    if request.cls is not None:
        request.cls.app = app
    ctx = app.app_context()
    ctx.push()

    db.drop_all()
    db.create_all()

    def teardown():
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        ctx.pop()

    request.addfinalizer(teardown)
    return db.session


def init_mysql_session(app, db, request):
    """Creates a new database session for a test."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{0}:{1}@{2}:{3}/{4}'.format(
        config.MYSQL_USER, config.MYSQL_PASSWORD, config.MYSQL_HOST, 3306, config.MYSQL_DATABASE_TEST
    )
    if request.cls is not None:
        request.cls.app = app
    ctx = app.app_context()
    ctx.push()

    truncate_db(db.engine)
    db.create_all()

    remove_foreign_keys(db)

    def teardown():
        db.session.rollback()
        db.session.remove()
        truncate_db(db.engine)
        ctx.pop()
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

    request.addfinalizer(teardown)
    return db.session


def remove_foreign_keys(db):
    inspector = reflection.Inspector.from_engine(db.engine)
    fake_metadata = MetaData()

    fake_tables = []
    all_fks = []

    for table_name in db.metadata.tables:
        fks = []
        for fk in inspector.get_foreign_keys(table_name):
            if fk['name']:
                fks.append(ForeignKeyConstraint((), (), name=fk['name']))
        t = Table(table_name, fake_metadata, *fks)
        fake_tables.append(t)
        all_fks.extend(fks)

    connection = db.engine.connect()
    transaction = connection.begin()
    for fkc in all_fks:
        connection.execute(DropConstraint(fkc))
    transaction.commit()


def truncate_db(engine):
    # delete all table data (but keep tables)
    # we do cleanup before test 'cause if previous test errored,
    # DB can contain dust
    meta = MetaData(bind=engine, reflect=True)
    con = engine.connect()
    trans = con.begin()
    con.execute('SET FOREIGN_KEY_CHECKS = 0;')
    for table in meta.sorted_tables:
        con.execute(table.delete())
    trans.commit()


def drop_all(engine):
    # drop all table
    meta = MetaData(bind=engine, reflect=True)
    con = engine.connect()
    trans = con.begin()
    meta.drop_all()
    trans.commit()


@pytest.fixture()
def session(app, db, request):
    """Creates a new database session for a test."""
    if 'session_class' in request.keywords:
        return
    return init_session(app, db, request)


@pytest.fixture(scope='class')
def session_class(app, db, request):
    """Creates a new database session for a test."""
    return init_session(app, db, request)


@pytest.fixture(scope='class')
def mysql_session(app, db, request):
    """Creates a new database session for a test."""
    return init_mysql_session(app, db, request)


@pytest.fixture()
def mysql_session_by_func(app, db, request):
    """Creates a new database session for a test."""
    return init_mysql_session(app, db, request)


def __drop_function(connection, function_name):
    connection.execute(f'DROP FUNCTION IF EXISTS {function_name};')


def __create_function(connection, function_name):
    connection.execute(f'DROP FUNCTION IF EXISTS {function_name};')
    with open(os.path.join(config.ROOT_DIR, 'catalog', 'utils', 'sql_functions', f'{function_name}.sql'), 'r') as file:
        sql = file.read()
        connection.execute(sql)


@pytest.fixture(scope='class')
def functions_product_details(db, request):
    """Creates all fuctions for product details"""

    connection = db.engine.connect()
    transaction = connection.begin()
    try:
        connection.execute('SET GLOBAL log_bin_trust_function_creators = 1;')
    except:
        # Just for local run, on server this configuration is initiated in docker
        pass
    __create_function(connection, 'IS_LAST_NOT_LAST_V2')
    __create_function(connection, 'GET_SEO_CONFIG_ID_V2')
    __create_function(connection, 'GET_SEO_DATA_V2')
    __create_function(connection, 'ATTRIBUTE_GROUP_V2')
    __create_function(connection, 'PRODUCT_GROUP_V2')
    transaction.commit()

    def teardown():
        connection = db.engine.connect()
        transaction = connection.begin()
        __drop_function(connection, 'PRODUCT_GROUP_V2')
        __drop_function(connection, 'ATTRIBUTE_GROUP_V2')
        __drop_function(connection, 'GET_SEO_DATA_V2')
        __drop_function(connection, 'GET_SEO_CONFIG_ID_V2')
        __drop_function(connection, 'IS_LAST_NOT_LAST_V2')
        transaction.commit()

    request.addfinalizer(teardown)


def login_patcher(user):
    """ Return a patcher to patch login

    :param user: the logged in user
    :return:
    """
    if user:
        current_seller_id = int(user.seller_ids.split(',')[0])
        login_user = login_manager.User(
            access_token='test',
            user_info=user,
            seller_id=current_seller_id,
        )
    else:
        login_user = flask_login.AnonymousUserMixin()

    def _get_user():
        return login_user

    patcher = mock.patch(
        'flask_login.utils._get_user',
        new=_get_user
    )
    return patcher


@pytest.fixture(autouse=True)
def prevent_call_ppm_api():
    """

    :return:
    """
    patcher = mock.patch('catalog.biz.ppm.call_ppm_api')
    call_api = patcher.start()
    call_api.return_value = 200
    yield
    patcher.stop()


@pytest.fixture(autouse=True)
def mock_get_temrinal_groups():
    with mock.patch('catalog.services.terminal.get_terminal_groups') as mock_getter:
        mock_getter.return_value = [{
            "sellerID": 1,
            "description": "",
            "id": 57,
            "isOwner": 1,
            "code": "AUTOTEST_SELLING_TERMINAL_GROUP",
            "type": "SELL",
            "sellerName": "",
            "isActive": 1,
            "name": "AUTOTEST_SELLING_TERMINAL_GROUP"
        }]
        yield


@pytest.fixture(autouse=True)
def mock_get_providers():
    with mock.patch('catalog.services.provider.get_provider_by_id') as mock_getter:
        mock_getter.return_value = {
            "id": 1,
            "displayName": "String",
            "isOwner": 0,
            "code": "Str",
            "logo": None,
            "createdAt": "2020-07-29 06:56:13",
            "slogan": "This is a string",
            "isActive": 1,
            "sellerID": 1,
            "name": "String",
            "updatedAt": "2020-07-29 06:56:13"
        }
        yield


@pytest.fixture(autouse=True)
def mock_get_seller_by_id():
    with mock.patch('catalog.services.seller.get_seller_by_id') as mock_getter:
        def my_side_effect(*args, **kwargs):
            fake_pv_seller = {
                'servicePackage': 'FBS',
                "districtCode": "7901",
                "autoProcessOrder": {
                    "isEnabled": False,
                    "needCheckStock": True,
                    "excludePaymentMethods": {
                    },
                    "excludeTerminals": {
                    }
                },
                "displayName": "Phong Vũ",
                "accountID": 851049,
                "code": "PVU",
                "wardCode": "790104",
                "provinceName": "Thành phố Hồ Chí Minh",
                "saleCategoryIDS": {
                },
                "wardName": "Phường Bến Thành",
                "districtName": "Quận 1",
                "name": "CÔNG TY CỔ PHẦN THƯƠNG MẠI DỊCH VỤ PHONG VŨ",
                "id": 1,
                "isActive": 1,
                "streetAddress": "Tầng 5, 117,119,121 Nguyễn Du",
                "logoUrl": "https://lh3.googleusercontent.com/qOnchEYD7No58bjEQs5pf_05IV-0DmoaCmEFXD007VHs5cn16LZ6PC98IlY3OiBL9UXsEwNzwiVHRrvSDMQ",
                "accountUpdated": 1,
                "internationalName": "PHONG VU TRADING - SERVICE CORPORATION",
                "provinceCode": "79",
                "isAutoGeneratedSKU": 0,
                "usingSystemCategory": 0,
                "fullAddress": "Tầng 5, 117,119,121 Nguyễn Du, Phường Bến Thành, Quận 1, Thành phố Hồ Chí Minh",
                "email": "cskh@phongvu.vn",
                "slogan": None,
                "usingGoodsManagementModules": 1,
                "phoneNumber": "02862908777",
                "taxIDNumber": "0304998358",
                "foundingDate": "2007-05-30",
                "brcDate": "2007-05-30",
                "brcCode": "0304998358"
            }
            if args[0] == 2:
                fake_pv_seller['id'] = 2
                fake_pv_seller['code'] = 'PVU2'
            return fake_pv_seller

        mock_getter.side_effect = my_side_effect
        yield


@pytest.fixture(scope='session')
def all_tests(request):
    process = int(request.config.getoption('--process'))
    total_processes = int(request.config.getoption('--total-processes'))

    total_tests = len(request.node.items)
    batch_count = total_tests // total_processes

    start = process * batch_count
    end = (process + 1) * batch_count if process != (total_processes - 1) else total_tests

    request.node.items[:] = request.node.items[start:end]
    yield


@pytest.fixture()
def mock_sellables_export_task_function():
    with mock.patch('catalog.biz.exporter.sellables_export_task') as mock_getter:
        mock_getter.return_value = None
        yield
