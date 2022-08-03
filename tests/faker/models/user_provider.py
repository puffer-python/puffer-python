# coding=utf-8

from tests.faker import fake
import faker.providers
from catalog import models


class UserProvider(faker.providers.BaseProvider):
    def user(self, seller_id=None, email=None):
        ret = models.User(
            seller_id=seller_id or fake.random_int(1,1000),
            email=email or fake.email()
        )
        models.db.session.add(ret)
        models.db.session.commit()
        return ret

    def iam_user(self, seller_id=None, seller_ids=None):
        user = models.IAMUser()
        user.name = fake.name()
        user.email = fake.email()
        user.seller_id = seller_id or fake.seller().id
        user.seller_ids = seller_ids or str(user.seller_id)
        user.access_token = fake.text(length=10)
        models.db.session.add(user)
        models.db.session.commit()

        return user
