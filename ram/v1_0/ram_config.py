VERSION = '1.0'
VERSION_TABLE = 'ram_version'

DEFAULT_EVENT_TABLE_NAME = 'ram_events'
DEFAULT_EVENT_LOG_TABLE_NAME = 'ram_event_logs'
DEFAULT_KEY = 'default'
DEFAULT_PARENT_KEY = 'default'
DEFAULT_MAX_RETRY_TIME = 10
DEFAULT_DELAY_TIME_WHEN_RETRIES = [1, 1, 2, 3, 5, 8, 13, 21, 34, 57]
MAX_EVENTS_SIZE = 1000
SECONDS_TO_SLEEP = 10

CREATE_VERSION_TABLE_SQL = 'CREATE TABLE ram_version ( ' \
                           'version varchar(255) NOT NULL, ' \
                           'created_at timestamp NOT NULL DEFAULT NOW() ' \
                           ')'

CREATE_EVENT_TABLE_SQL = 'CREATE TABLE `{table_name}` ( ' \
                         '`id` bigint NOT NULL AUTO_INCREMENT, ' \
                         '`ref` varchar(255) NULL, ' \
                         '`parent_key` varchar(255) NOT NULL, ' \
                         '`key` varchar(255) NOT NULL, ' \
                         '`type` int NOT NULL, ' \
                         '`status` varchar(255) NOT NULL,    ' \
                         '`retry_count` int DEFAULT NULL, ' \
                         '`payload` text DEFAULT NULL, ' \
                         '`created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, ' \
                         '`updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP, ' \
                         '`want_to_send_after` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP, ' \
                         'PRIMARY KEY (`id`)' \
                         ')'
CREATE_INDEX_EVENT_TABLE_SQL = 'CREATE INDEX {table_name}_parent_key_want_to_send_after ' \
                               'ON `{table_name}` (`parent_key`, `want_to_send_after`)'

CREATE_EVENT_LOG_TABLE_SQL = 'CREATE TABLE `{table_name}` (' \
                             '  `id` bigint NOT NULL AUTO_INCREMENT,' \
                             '  `event_id` bigint NOT NULL,' \
                             '  `event_ref` varchar(255) NULL,' \
                             '  `event_parent_key` varchar(255) NOT NULL,' \
                             '  `event_key` varchar(255) NOT NULL,' \
                             '  `event_type` int NOT NULL,' \
                             '  `event_status` varchar(255) NOT NULL,' \
                             '  `event_retry_count` int DEFAULT NULL,' \
                             '  `event_payload` text DEFAULT NULL,' \
                             '  `event_created_at` timestamp NULL,' \
                             '  `event_updated_at` timestamp NULL,' \
                             '  `event_want_to_send_after` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,' \
                             '  `status` varchar(255) NOT NULL,' \
                             '  `error_message` text DEFAULT NULL,' \
                             '  `start_timestamp` timestamp NULL,' \
                             '  `finish_timestamp` timestamp NULL,' \
                             '  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,' \
                             '  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,' \
                             '  PRIMARY KEY (`id`)' \
                             ')'
CREATE_INDEX1_EVENT_LOG_TABLE_SQL = 'CREATE INDEX {table_name}_updated_at ON `{table_name}` (`updated_at`)'
CREATE_INDEX2_EVENT_LOG_TABLE_SQL = 'CREATE INDEX {table_name}_event_key ON `{table_name}` (`event_key`, `updated_at`)'
CREATE_INDEX3_EVENT_LOG_TABLE_SQL = 'CREATE INDEX {table_name}_event_ref ON `{table_name}` (`event_ref`)'

INSERT_EVENT_LOG_SQL = '''INSERT INTO `{event_log_table_name}` (
                        `event_id`,
                        `event_ref`,
                        `event_parent_key`,
                        `event_key`,
                        `event_type`,
                        `event_status`,
                        `event_retry_count`,
                        `event_payload`,
                        `event_created_at`,
                        `event_updated_at`,
                        `event_want_to_send_after`,
                        `status`,
                        `error_message`,
                        `start_timestamp`,
                        `finish_timestamp`
                    )
                    SELECT  
                        `id`,
                        `ref`,
                        `parent_key`,
                        `key`,
                        `type`,
                        `status`,
                        `retry_count`,
                        `payload`,
                        `created_at`,
                        `updated_at`,
                        `want_to_send_after`,
                        :status,
                        :error_message,
                        now() - INTERVAL {processed_seconds} SECOND,
                        now()
                    FROM `{event_table_name}` where `id` = :id
'''

DELETE_EVENT_SQL = 'delete from `{table_name}` where id = :id'

UPDATE_EVENT_SQL = '''update `{table_name}` set `retry_count` = :retry_count, `status`= 'NEED RETRY', 
                        want_to_send_after = now() + INTERVAL :delay_seconds SECOND where id = :id'''

LOG_STATUS_SUCCESS = 'success'
LOG_STATUS_FAIL_AND_RETRY = 'fail and retry'
LOG_STATUS_FAIL_AND_DONE = 'fail and done'
