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
