import os

from ram.v1_0.ram_config import DEFAULT_EVENT_TABLE_NAME, DEFAULT_EVENT_LOG_TABLE_NAME


class MySqlConfig:

    def __init__(self, database=None, host=None,
                 password=None, user=None, port=None,
                 event_table_name=None, event_log_table_name=None):
        self.database = None
        self.host = None
        self.password = None
        self.user = None
        self.port = None
        self.event_table_name = None
        self.event_log_table_name = None
        self.load_config('database', database, 'MYSQL_DATABASE')
        self.load_config('host', host, 'MYSQL_HOST')
        self.load_config('password', password, 'MYSQL_PASSWORD')
        self.load_config('user', user, 'MYSQL_USER')
        self.load_config('port', port, 'MYSQL_FORWARD_PORT', '3306')
        self.load_config('event_table_name', event_table_name, 'MYSQL_EVENT_TABLE_NAME', DEFAULT_EVENT_TABLE_NAME)
        self.load_config('event_log_table_name', event_log_table_name,
                         'MYSQL_EVENT_LOG_TABLE_NAME', DEFAULT_EVENT_LOG_TABLE_NAME)

    def load_config(self, attribute_name, value, config_key, value_default=None):
        attribute_value = value if value is not None else os.environ.get(config_key, None)
        attribute_value = attribute_value if attribute_value is not None else value_default
        if attribute_value is None:
            raise Exception(f'You need pass {attribute_name} param when init MySqlConfig or set it in'
                            f' {config_key} param at system environment')
        setattr(self, attribute_name, attribute_value)
