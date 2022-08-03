from tests.faker import fake
from faker.providers import BaseProvider
from catalog import models


class SellableProductShippingTypeProvider(BaseProvider):
    def sellable_product_shipping_type(self, sellable_product_id, shipping_type_id=None):
        entity = models.SellableProductShippingType(
            sellable_product_id=sellable_product_id or fake.sellable_product().id,
            shipping_type_id=shipping_type_id or fake.shipping_type().id
        )

        models.db.session.add(entity)
        models.db.session.commit()

        return entity
