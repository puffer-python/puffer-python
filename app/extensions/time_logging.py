import datetime
import functools
import logging
import time
from sqlalchemy import event
from sqlalchemy.engine import Engine

__author__ = 'Chung.Hd'

logger = logging.getLogger('time_logging')
logger.setLevel(logging.DEBUG)

def time_logging(f):
    @functools.wraps(f)
    def wrapper(*args, **kw):
        logger.debug('TIME LOGGING START'.center(80, "="))
        logger.debug(f'Function {f.__name__}')
        logger.debug(f'Start at {datetime.datetime.now()}')

        ts = time.time()
        result = f(*args, **kw)
        te = time.time()

        logger.debug('TIME LOGGING END'.center(80, "="))
        logger.debug(f'Function {f.__name__}')
        logger.debug(f"Arguments: {args}")
        logger.debug(f"Keywords: {kw}")
        logger.debug(f"Total time: {te - ts} sec")

        return result

    return wrapper


class TimeCounter(object):
    """
    Usage:
        time_counter = TimeCounter()
        sleep(5)
        print("process time:", time_counter)

    Result:
        process time: 5.0s
    """

    __instance = None
    _starts = {}
    _auto_index = 0

    @staticmethod
    def get_instance():
        if not TimeCounter.__instance:
            TimeCounter()
        return TimeCounter.__instance

    def __init__(self):
        if TimeCounter.__instance:
            return TimeCounter.__instance
        else:
            TimeCounter.__instance = self

    def print(self, key = None, note="", drop_key = True):
        if not key:
            key = list(self._starts)[-1] if len(self._starts) > 0 else None
        if not self._starts.get(key):
            logger.debug("Start time for this key is not set yet")
            return
        rt = (datetime.datetime.now() - self._starts[key]).total_seconds()
        if drop_key:
            del self._starts[key]
        key = '%s - %s' % (key, note)
        logger.debug(f"Key {key} total process time: {rt}")
        logger.debug(f"Key {key} total process time: {rt}")
        return rt

    def __repr__(self):
        return "\n".join(
            ["%s: %s %s %s" % (key, self._starts[key], datetime.datetime.now(), (datetime.datetime.now() - self._starts[key]).total_seconds())
             for key in self._starts])

    def mark(self, key=None):
        if not key:
            key = "auto-logging-key-%s" % self._auto_index
            self._auto_index += 1
        logger.debug(f"Start logging for key {key}")
        logger.debug(f"Start logging for key {key}")
        self._starts[key] = datetime.datetime.now()


def enable_sqlalchemy_runtime_logging():
    @event.listens_for(Engine, "before_cursor_execute")
    def before_cursor_execute(conn, cursor, statement,
                              parameters, context, executemany):
        conn.info.setdefault('query_start_time', []).append(time.time())

    @event.listens_for(Engine, "after_cursor_execute")
    def after_cursor_execute(conn, cursor, statement,
                             parameters, context, executemany):
        total = time.time() - conn.info['query_start_time'].pop(-1)
        if total > 0.05:
            logger.debug(f"DB QUERY SLOW {total:.5f}".center(80, "="))
            logger.debug(statement)
