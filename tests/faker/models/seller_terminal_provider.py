# coding=utf-8
import random

from faker.providers import BaseProvider

from catalog.models import (
    db,
    SellerTerminal
)
from tests.faker import fake


class SellerTerminalProvider(BaseProvider):
    def seller_terminal(self, seller_id=None, terminal_id=None):
        ret = SellerTerminal()
        ret.seller_id = seller_id or fake.seller().id
        ret.terminal_id = terminal_id or fake.terminal().id
        ret.is_requested_approval = random.choice([True, False])
        ret.is_owner = random.choice([True, False])
        db.session.add(ret)
        db.session.commit()
        return ret
