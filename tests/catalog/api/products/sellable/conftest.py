# coding=utf-8
import logging
import pytest

from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def populate_on_off_status(session):
    for status_code in ('on', 'off', 'pending', 'inactive'):
        status = m.Misc()
        status.type = 'on_off_status'
        status.code = status_code
        m.db.session.add(status)

    m.db.session.commit()


@pytest.fixture(scope='class')
def populate_on_off_status_class_scope(session_class):
    for status_code in ('on', 'off', 'pending', 'inactive'):
        status = m.Misc()
        status.type = 'on_off_status'
        status.code = status_code
        m.db.session.add(status)

    m.db.session.commit()

