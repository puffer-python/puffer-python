# coding=utf-8
import logging
import requests
import config
from catalog.extensions import exceptions as exc
from catalog.extensions.flask_cache import cache
from catalog.models import (
    db,
    Terminal
)

_logger = logging.getLogger(__name__)


def create_or_update_terminal(data):
    terminal_id = data.get('id')
    terminal = get_terminal(terminal_id)

    if terminal is not None:
        if terminal.code != data.get('code'):
            raise exc.BadRequestException('Invalid code')

        message = 'Cập nhật terminal thành công'
    else:
        terminal = Terminal()
        message = 'Tạo mới terminal thành công'

    # Save to db
    for key, value in data.items():
        if hasattr(terminal, key):
            setattr(terminal, key, value)
    db.session.add(terminal)
    db.session.commit()
    return terminal, message


def get_terminal(terminal_id):
    terminal = Terminal.query.filter(
        Terminal.id == terminal_id
    ).first()

    return terminal


def create_terminal(name, code, seller_id):
    if Terminal.query.filter(Terminal.code == code).first():
        raise exc.BadRequestException('Terminal existed')
    terminal = Terminal(
        name=name,
        code=code,
        seller_id=seller_id
    )
    db.session.add(terminal)
    db.session.commit()
    return terminal


def get_terminal_groups(seller_id, size=200, group_type='PRICE', is_active=1):
    params = {
        'page': 1,
        'pageSize': size,
        'type': group_type,
        'isActive': is_active
    }
    url = '{}/sellers/{}/terminal-groups'.format(
        config.SELLER_API,
        seller_id
    )

    try:
        resp = requests.get(url, params, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError(f'Seller service raise exception {resp.text}')
    except (requests.exceptions.RequestException, RuntimeError) as ex:
        _logger.exception(ex)
        return []
    else:
        data = resp.json()
        return data.get('result', {}).get('terminalGroups', [])
