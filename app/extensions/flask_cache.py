import os

from flask_caching import Cache

import config

cache = Cache(
    config={
        'CACHE_TYPE': config.CACHE_TYPE,
        'CACHE_REDIS_URL': config.CACHE_REDIS_URL})


def init_cache(app):
    """
    Init flask-caching from Flask application. Clear the current cache

    :param  app:
    :return: cache
    """
    cache.init_app(app)
    with app.app_context():
        cache.clear()
    return cache
