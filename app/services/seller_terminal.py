# coding=utf-8

from catalog.extensions import exceptions as exc
from catalog.models import (
    db,
    SellerTerminal)


def create_or_update_seller_terminal(data):
    seller_terminal_id = data.get('id')
    seller_terminal = get_seller_terminal(seller_terminal_id)

    if seller_terminal is not None:
        if seller_terminal.seller_id != data.get('seller_id') or seller_terminal.terminal_id != data.get('terminal_id'):
            raise exc.BadRequestException('Invalid terminal id or seller id')

        messsage = 'Cập nhật seller terminal thành công'
    else:
        seller_terminal = SellerTerminal()
        messsage = 'Tạo mới seller terminal thành công'

    # Save to db
    for key, value in data.items():
        if hasattr(seller_terminal, key):
            setattr(seller_terminal, key, value)
    db.session.add(seller_terminal)
    db.session.commit()
    return seller_terminal, messsage


def get_seller_terminal(seller_terminal_id):
    seller_terminal = SellerTerminal.query.filter(
        SellerTerminal.id == seller_terminal_id
    ).first()

    return seller_terminal


def delete_seller_terminal(data):
    seller_terminal_id = data.get('id')
    seller_terminal = get_seller_terminal(seller_terminal_id)

    if seller_terminal is None:
        raise exc.BadRequestException('Seller terminal does not exist')

    if seller_terminal.seller_id != data.get('seller_id') or seller_terminal.terminal_id != data.get('terminal_id'):
        raise exc.BadRequestException('Invalid terminal id or seller id')

    SellerTerminal.query.filter(
        SellerTerminal.id == seller_terminal_id,
    ).delete()

    db.session.commit()

    return seller_terminal_id
