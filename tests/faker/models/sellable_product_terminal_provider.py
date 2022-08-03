#coding=utf-8

from faker.providers import BaseProvider
from tests.faker import fake
from catalog.models import (
    db,
    SellableProductTerminal, SellableProductSeoInfoTerminal
)

class SellableProductTerminalProvider(BaseProvider):
    def sellable_product_terminal(self, sellable_product_id=None, terminal_id=None, terminal_code=None, apply_seller_id=None):
        if sellable_product_id is None:
            sellable_product_id = fake.sellable_product().id

        if terminal_id is None:
            terminal = fake.terminal()
            terminal_id = terminal.id
            terminal_code = terminal.code

        if apply_seller_id is None:
            apply_seller_id = fake.seller().id

        seo = SellableProductTerminal(
            sellable_product_id=sellable_product_id,
            terminal_id=terminal_id,
            terminal_code=terminal_code,
            apply_seller_id=apply_seller_id
        )

        seo.description = fake.text()
        seo.display_name = fake.name()
        seo.meta_description = fake.text()
        seo.meta_keyword = fake.text()
        seo.short_description = fake.text()
        seo.short_description_after = fake.text()
        seo.short_description_before = fake.text()

        db.session.add(seo)
        db.session.flush()
        return seo
