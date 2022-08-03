from tests.faker import fake
from faker.providers import BaseProvider
from catalog import models as m


class ProductCategoryProvider(BaseProvider):
    def product_category(self, product_id=None, category_id=None, created_by=None):
        ret = m.ProductCategory(
            product_id=product_id or fake.product().id,
            category_id=category_id or fake.category().id,
            created_by=created_by or fake.text()
        )

        m.db.session.add(ret)
        m.db.session.commit()

        return ret