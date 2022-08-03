from datetime import datetime
import logging
import time
import traceback

from sqlalchemy import create_engine, text

from catalog.utils.lambda_list import LambdaList
from ram.v1_0.mysql_config import MySqlConfig
from ram.v1_0.producer.ram_producer import get_version_in_database
from ram.v1_0.ram_config import DEFAULT_PARENT_KEY, DEFAULT_MAX_RETRY_TIME, DEFAULT_DELAY_TIME_WHEN_RETRIES, \
    VERSION_TABLE, VERSION, MAX_EVENTS_SIZE, SECONDS_TO_SLEEP, LOG_STATUS_SUCCESS, \
    INSERT_EVENT_LOG_SQL, DELETE_EVENT_SQL, LOG_STATUS_FAIL_AND_RETRY, LOG_STATUS_FAIL_AND_DONE, UPDATE_EVENT_SQL
from ram.v1_0.ram_event import RamEvent
from ram.v1_0.ram_exception import RamException
from ram.v1_0.stop_retry_exception import StopRetryException

logger = logging.getLogger('ram_consumer')
DEFAULT_MAX_LENGTH = 255


class RamConsumer:

    def __init__(self, mysql_config=None, parent_key=None,
                 map_event_key_with_handler={}, max_retry_time=None,
                 delay_time_when_retries=None, repeat_time=None,
                 sleep_time_if_no_event=None):

        self.mysql_config = mysql_config if mysql_config else MySqlConfig()
        self.db_engine = create_engine(f'mysql+pymysql://{self.mysql_config.user}:{self.mysql_config.password}'
                                       f'@{self.mysql_config.host}:{self.mysql_config.port}'
                                       f'/{self.mysql_config.database}')

        self.sleep_time_if_no_event = sleep_time_if_no_event or SECONDS_TO_SLEEP
        self.repeat_time = repeat_time
        self.parent_key = parent_key or DEFAULT_PARENT_KEY

        self.map_event_key_with_handler = map_event_key_with_handler
        self.event_keys = self.map_event_key_with_handler.keys()

        self.max_retry_time = max_retry_time or DEFAULT_MAX_RETRY_TIME

        self.delay_time_when_retries = delay_time_when_retries or DEFAULT_DELAY_TIME_WHEN_RETRIES

        self.__validate_init(parent_key, map_event_key_with_handler, max_retry_time)

    def __table_exists(self, conn, table_name):
        results = conn.execute(text('select 1 from INFORMATION_SCHEMA.TABLES where table_schema = :schema_name'
                                    ' and table_name = :table_name'), schema_name=self.mysql_config.database,
                               table_name=table_name)
        return results.rowcount > 0

    def start(self):
        logger.info('Start run consumer')
        logger.info(f'The parent key event is: {self.parent_key}')
        logger.info(f'the event key need handling is: [{LambdaList(self.event_keys).string_join(",")}]')

        count = 0
        while self.repeat_time is None or count < self.repeat_time:
            try:
                count += 1
                logger.info(f'process turn {count} ')
                logger.info(f'Reading table {self.mysql_config.event_table_name}')
                events = self.__get_events()
                logger.info(f'There is {len(events)} events')
                for event in events:
                    self.__process(event)
                logger.info(f'finished turn {count} ')
                if not events:
                    time.sleep(self.sleep_time_if_no_event)
            except Exception as ex:
                logger.exception(msg='there is error at consumer process', exc_info=ex)
                time.sleep(self.sleep_time_if_no_event * 10)

    def __get_events(self):
        with self.db_engine.connect() as conn:
            results = conn.execute(text(f'''select `id`, `ref`, `parent_key`, `key`, `type`, `status`, `retry_count`, 
                        `payload`, `created_at`, `updated_at`, `want_to_send_after` 
                         from `{self.mysql_config.event_table_name}` where `parent_key` = :parent_key 
                         and `key` in :keys and `want_to_send_after` < now() order by `want_to_send_after`'''),
                                   parent_key=self.parent_key, keys=tuple(self.event_keys))
            return [RamEvent(r) for r in results]

    def __process(self, event):
        start_timestamp = self.__get_current_timestamp()
        try:
            self.map_event_key_with_handler[event.key](event.payload)
            self.__event_success(event, (self.__get_current_timestamp() - start_timestamp).total_seconds())
        except Exception as ex:
            process_time = (self.__get_current_timestamp() - start_timestamp).total_seconds()
            self.__event_fail(event, process_time, ex)

    def __event_success(self, event, processed_seconds):
        with self.db_engine.connect() as conn:
            with conn.begin() as transaction:
                self.__insert_log(event_id=event.id, status=LOG_STATUS_SUCCESS,
                                  processed_seconds=processed_seconds, error_message='',
                                  connection=conn)
                self.__remove_event(event, conn)
                transaction.commit()

    def __insert_log(self, event_id, status, processed_seconds, error_message, connection):
        error_message = '' if error_message is None else error_message
        insert_query = INSERT_EVENT_LOG_SQL.format(event_log_table_name=self.mysql_config.event_log_table_name,
                                                   event_table_name=self.mysql_config.event_table_name,
                                                   processed_seconds=processed_seconds)
        connection.execute(text(insert_query), id=event_id, status=status, error_message=error_message)

    def __remove_event(self, event, connection):
        delete_query = DELETE_EVENT_SQL.format(table_name=self.mysql_config.event_table_name)
        connection.execute(text(delete_query), id=event.id)

    @staticmethod
    def __get_current_timestamp():
        return datetime.now()

    def __event_fail(self, event, processed_seconds, ex):
        retry_count = 0 if event.retry_count is None else event.retry_count
        if isinstance(ex, RamException):
            exc_str = str(ex)
        else:
            exc_str = "".join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__))
        status = LOG_STATUS_FAIL_AND_RETRY

        stop_retry = (retry_count >= self.max_retry_time) or isinstance(ex, StopRetryException)
        if stop_retry:
            status = LOG_STATUS_FAIL_AND_DONE
        with self.db_engine.connect() as conn:
            with conn.begin() as transaction:
                self.__insert_log(event_id=event.id, status=status,
                                  processed_seconds=processed_seconds, error_message=exc_str,
                                  connection=conn)
                if stop_retry:
                    self.__remove_event(event, conn)
                else:
                    self.__update_event(event, conn)
                transaction.commit()

    def __update_event(self, event, connection):
        retry_count = 0 if event.retry_count is None else event.retry_count
        update_query = UPDATE_EVENT_SQL.format(table_name=self.mysql_config.event_table_name)
        connection.execute(text(update_query), id=event.id, retry_count=retry_count + 1,
                           delay_seconds=self.delay_time_when_retries[retry_count] * 60)

    def __validate_init(self, parent_key, map_event_key_with_handler, max_retry_time):

        self.__validate_max_length(parent_key, 'length of parent_key must be below 256')

        for key in map_event_key_with_handler:
            self.__validate_max_length(key, 'length of event_key in map_event_key_with_handler must be below 256')
            func = map_event_key_with_handler[key]
            if not callable(func):
                raise Exception('must pass handler function in map_event_key_with_handler')

        if max_retry_time is not None and max_retry_time <= 0:
            raise Exception('max_retry_time must be larger than 0')

        if len(self.delay_time_when_retries) != self.max_retry_time:
            raise Exception('delay_time_when_retries need has length equals max_retry_time')

        with self.db_engine.connect() as conn:
            if not self.__table_exists(conn, VERSION_TABLE):
                raise Exception(f'{VERSION_TABLE} table is not exists')

            version_in_database = get_version_in_database(conn)
            if version_in_database is None:
                raise Exception(f'can not find version in database')
            if version_in_database != VERSION:
                raise Exception(f'Your database already use other version of RAM: version {version_in_database}. '
                                f'You current ram consumer version is {VERSION}')

            if not self.__table_exists(conn, self.mysql_config.event_table_name):
                raise Exception(f'{self.mysql_config.event_table_name} table is not exists')

            if not self.__table_exists(conn, self.mysql_config.event_log_table_name):
                raise Exception(f'{self.mysql_config.event_log_table_name} table is not exists')

    @staticmethod
    def __validate_max_length(key, message, max_length=DEFAULT_MAX_LENGTH):
        if key and len(key) > max_length:
            raise Exception(message)
