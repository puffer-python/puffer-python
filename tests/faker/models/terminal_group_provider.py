import random

from faker.providers import BaseProvider
from catalog import models
from catalog.models import db
from tests.faker import fake


class TerminalGroupProvider(BaseProvider):
    def terminal_group(self, **kwargs):
        ret = models.TerminalGroup(
            code=kwargs.get('code', fake.text()),
            name=kwargs.get('name', fake.text()),
            seller_id=kwargs.get('seller_id', fake.seller().id),
            is_active=kwargs.get('is_active', True),
            type=kwargs.get('type', 'SELL')
        )
        db.session.add(ret)
        db.session.flush()

        return ret

    def sellable_product_terminal_group(self, **kwargs):
        terminal_group = kwargs.get('terminal_group', fake.terminal_group())
        sellable_product = kwargs.get('sellable_product', fake.sellable_product(seller_id=terminal_group.seller_id))
        ret = models.SellableProductTerminalGroup(
            terminal_group_code=terminal_group.code,
            sellable_product_id=kwargs.get('sellable_product_id', sellable_product.id),
            created_by=kwargs.get('user').email if kwargs.get('user') else None,
            updated_by=kwargs.get('user').email if kwargs.get('user') else None,
        )
        db.session.add(ret)
        db.session.flush()

        return ret

    def seller_terminal_group(self, group_id=None, seller_id=None):
        ret = models.SellerTerminalGroup()
        ret.terminal_group_id = group_id if group_id is not None else fake.terminal_group().id
        ret.seller_id = seller_id if seller_id is not None else fake.seller().id
        models.db.session.add(ret)
        models.db.session.flush()
        return ret

    def terminal_group_mapping(self, terminal_code=None, group_code=None):
        ret = models.TerminalGroupTerminal()
        ret.terminal_code = terminal_code if terminal_code is not None else fake.terminal().code
        ret.terminal_group_code = group_code if group_code is not None else fake.terminal_group().code
        models.db.session.add(ret)
        models.db.session.commit()
        return ret
