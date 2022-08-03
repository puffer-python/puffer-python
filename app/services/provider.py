# coding=utf-8

import requests
import config
from catalog.extensions.flask_cache import cache


@cache.memoize(timeout=300)
def get_provider_by_id(provider_id):
    url = f'{config.SELLER_API}/providers/{provider_id}'
    try:
        resp = requests.get(url, timeout=2)
    except requests.Timeout:
        return None
    else:
        return resp.json().get('result', {}).get('provider')
