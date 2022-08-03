# pylint: disable=no-member
# pylint: disable=no-name-in-module

import json
import logging
from collections import Mapping # pylint: disable=no-name-in-module
from datetime import timedelta, datetime
from catalog.models.ram_event import RamEvent

from sqlalchemy import create_engine, text

from ram.v1_0.ram_config import (
    VERSION_TABLE, CREATE_VERSION_TABLE_SQL, VERSION, CREATE_EVENT_TABLE_SQL,
    CREATE_INDEX_EVENT_TABLE_SQL, CREATE_EVENT_LOG_TABLE_SQL,
    CREATE_INDEX1_EVENT_LOG_TABLE_SQL,
    CREATE_INDEX2_EVENT_LOG_TABLE_SQL, CREATE_INDEX3_EVENT_LOG_TABLE_SQL,
    DEFAULT_PARENT_KEY, DEFAULT_KEY
)
from ram.v1_0.mysql_config import MySqlConfig

__author__ = 'Dung.BV'
_logger = logging.getLogger(__name__)


def create_version_table(conn):
    conn.execute(CREATE_VERSION_TABLE_SQL)


def get_version_in_database(conn):
    results = conn.execute(f'select version from {VERSION_TABLE}')
    rowcount = results.rowcount
    if rowcount == 0:
        return None
    elif rowcount == 1:
        return results.first()[0]
    else:
        raise Exception(f'there is more than 1 record in {VERSION_TABLE} table. It should be has only 1 record '
                        f'if RAM database already is created '
                        f'or 0 record if it is first time RAM was used with this database')


def insert_to_version_table(conn):
    with conn.begin() as transaction:
        conn.execute(f'insert into {VERSION_TABLE} (version) values ({VERSION})')
        transaction.commit()


class RamProducer:

    def __init__(self, mysql_config=None, connection=None, map_key_with_parent={}):
        if map_key_with_parent is None:
            map_key_with_parent = {}
        if not isinstance(map_key_with_parent, dict):
            raise Exception('map_key_with_parent must be dict type')
        for key in map_key_with_parent:
            if len(key) > 255:
                raise Exception('length of event_key in map_key_with_parent must be below 256')
            if len(map_key_with_parent[key]) > 255:
                raise Exception('length of event_parent_key in map_key_with_parent must be below 256')

        self.__dic_key_parent_key = map_key_with_parent
        self.mysql_config = mysql_config if mysql_config else MySqlConfig()
        self.db_engine = create_engine(f'mysql+pymysql://{self.mysql_config.user}:{self.mysql_config.password}'
                                       f'@{self.mysql_config.host}:{self.mysql_config.port}'
                                       f'/{self.mysql_config.database}')
        self.connection = connection

        with self.db_engine.connect() as conn:
            if not self.__table_exists(conn, VERSION_TABLE):
                create_version_table(conn)
            version_in_database = get_version_in_database(conn)
            if version_in_database is None:
                insert_to_version_table(conn)
            else:
                if version_in_database != VERSION:
                    raise Exception(f'Your database already use other version of RAM: version {version_in_database}. '
                                    f'You need use matching version ram lib if your correct version is '
                                    f'{version_in_database}. Otherwise, you need drop/rename {VERSION_TABLE} table '
                                    f'or delete all record in {VERSION_TABLE} table.')

            if not self.__table_exists(conn, self.mysql_config.event_table_name):
                self.__create_event_table(conn)

            if not self.__table_exists(conn, self.mysql_config.event_log_table_name):
                self.__create_event_log_table(conn)

    def __table_exists(self, conn, table_name):
        results = conn.execute(text('select 1 from INFORMATION_SCHEMA.TABLES where table_schema = :schema_name'
                                    ' and table_name = :table_name'), schema_name=self.mysql_config.database,
                               table_name=table_name)
        return results.rowcount > 0

    def __create_event_table(self, conn):
        sql_create_table = CREATE_EVENT_TABLE_SQL.format(table_name=self.mysql_config.event_table_name)
        conn.execute(sql_create_table)
        sql_create_index = CREATE_INDEX_EVENT_TABLE_SQL.format(table_name=self.mysql_config.event_table_name)
        conn.execute(sql_create_index)

    def __create_event_log_table(self, conn):
        sql_create_table = CREATE_EVENT_LOG_TABLE_SQL.format(table_name=self.mysql_config.event_log_table_name)
        conn.execute(sql_create_table)
        sql_create_index1 = CREATE_INDEX1_EVENT_LOG_TABLE_SQL.format(table_name=self.mysql_config.event_log_table_name)
        conn.execute(sql_create_index1)
        sql_create_index2 = CREATE_INDEX2_EVENT_LOG_TABLE_SQL.format(table_name=self.mysql_config.event_log_table_name)
        conn.execute(sql_create_index2)
        sql_create_index3 = CREATE_INDEX3_EVENT_LOG_TABLE_SQL.format(table_name=self.mysql_config.event_log_table_name)
        conn.execute(sql_create_index3)

    def send(self, connection=None, event_parent_key=None, event_key=None,
             ref='', message=None, delay_milliseconds=0):
        event_key = event_key if event_key is not None else DEFAULT_KEY
        if message is None or ((type(message) is str) and (message == '')):
            raise Exception('message cannot be None or empty')
        if len(event_key) > 255:
            raise Exception('length of event_key must be below 256')
        if event_parent_key is not None and len(event_parent_key) > 255:
            raise Exception('length of event_parent_key must be below 256')
        if delay_milliseconds < 0:
            raise Exception('delay_milliseconds must be larger than or equal 0')
        if isinstance(message, Mapping):
            json_message = json.dumps(message)
        elif hasattr(message, '__dict__'):
            json_message = json.dumps(message.__dict__)
        else:
            json_message = str(message)
        parent_key = event_parent_key if event_parent_key else self.__get_parent_key(event_key)
        conn = connection if connection is not None else self.connection
        if not conn:
            raise Exception('You must pass connection on send function or init function')
        ram_event = RamEvent()
        ram_event.ref = ref
        ram_event.parent_key = parent_key
        ram_event.key = event_key
        ram_event.type = 1
        ram_event.status = 'CREATED'
        ram_event.payload = json_message
        ram_event.want_to_send_after = datetime.now() + timedelta(milliseconds=delay_milliseconds)
        conn.add(ram_event)
        conn.commit()

    def send_by_select(self, connection=None, select_stmt=None):
        conn = connection if connection is not None else self.connection
        if not conn:
            raise Exception('You must pass connection on send function or init function')
        if not select_stmt:
            raise Exception('Select command cannot be None')
        sql = f'''INSERT INTO {self.mysql_config.event_table_name}
                    (
                    `ref`,
                    `parent_key`,
                    `key`,
                    `type`,
                    `status`,
                    `payload`,
                    `want_to_send_after`
                    ) {select_stmt}'''
        conn.execute(text(sql))
        conn.commit()

    def __get_parent_key(self, event_key):
        parent_key = self.__dic_key_parent_key[event_key] \
            if self.__dic_key_parent_key and (event_key in self.__dic_key_parent_key) else DEFAULT_PARENT_KEY
        return parent_key
