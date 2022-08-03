from tests.faker import fake
from faker.providers import BaseProvider
from catalog import models


class CategoryShippingTypeProvider(BaseProvider):
    def category_shipping_type(self, category_id, shipping_type_id=None):
        entity = models.CategoryShippingType(
            category_id=category_id or fake.category().id,
            shipping_type_id=shipping_type_id or fake.shipping_type().id
        )

        models.db.session.add(entity)
        models.db.session.commit()

        return entity
