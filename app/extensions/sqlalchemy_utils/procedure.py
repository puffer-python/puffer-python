# coding=utf-8
import logging
from flask import current_app as app
from sqlalchemy import create_engine

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


def exec_procedure(proc_name, params):
    """
    Execute the stored procedure with args

    :param proc_name:
    :param params:
    :return:
    """
    engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    connection = engine.raw_connection()
    try:
        cursor = connection.cursor()
        cursor.callproc(proc_name, [params])
        cursor.close()
        connection.commit()
    except Exception as e:
        _logger.exception(e)
        raise e
    finally:
        connection.close()
