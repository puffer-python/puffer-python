# coding=utf-8
import datetime
import logging
import random

from faker.providers import BaseProvider
from tests.faker import fake
from catalog import models as m

__author__ = 'Kien.HT'
_logger = logging.getLogger(__name__)


class TerminalProvider(BaseProvider):
    def terminal(self, sellable_ids=None, seller_id=None, terminal_type=None,
                 is_active=None, updated_at=None, terminal_code=None, terminal_id=None, add_seo=True):
        ret = m.Terminal()
        ret.name = fake.text()
        ret.code = terminal_code if terminal_code is not None else fake.text()
        ret.seller_id = seller_id or fake.seller().id
        ret.type = terminal_type or random.choice([
            'showroom',
            'online'
        ])
        ret.platform = fake.text()
        ret.full_address = fake.text()
        ret.is_requested_approval = random.choice([True, False])
        ret.is_active = is_active if is_active is not None else random.choice([True, False])
        ret.updated_at = updated_at or datetime.datetime(2019, 1, 1, 0, 0, 0)
        m.db.session.add(ret)
        m.db.session.flush()

        if sellable_ids:
            for sellable_id in sellable_ids:
                assoc = m.SellableProductTerminal()
                assoc.sellable_product_id = sellable_id
                assoc.terminal_id = ret.id
                assoc.terminal_type = ret.type
                assoc.terminal_code = ret.code
                assoc.display_name = fake.text()
                assoc.meta_title = fake.text()
                assoc.meta_description = fake.text()
                assoc.meta_keyword = fake.text()
                assoc.on_off_status = random.choice([
                    'on', 'off', 'pending', 'inactive'
                ])
                m.db.session.add(assoc)

                if add_seo:
                    seo = m.SellableProductSeoInfoTerminal()
                    seo.sellable_product_id = sellable_id
                    seo.terminal_id = terminal_id if terminal_id is not None else ret.id
                    seo.terminal_code = ret.code

                    seo.display_name = fake.text()
                    seo.meta_title = fake.text()
                    seo.meta_description = fake.text()
                    seo.meta_keyword = fake.text()
                    seo.description = fake.text()
                    seo.short_description = fake.text()
                    seo.url_key = fake.text()
                    seo.created_by = fake.email()

                    m.db.session.add(seo)

        m.db.session.commit()
        return ret
