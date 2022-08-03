# coding=utf-8
import random
import string
import uuid
import datetime
import time

from faker import (
    Faker,
    providers
)


class Provider(providers.BaseProvider):
    def id(self):
        return random.randrange(1, 10000000)

    def float(self, max=1000):
        return random.uniform(0, max)

    def integer(self, max=1000):
        max = max or 1000
        return random.randint(0, max)

    def text(self, length=None, allow_characters=None):
        length = 10 if length is None else length
        if allow_characters is None:
            allow_characters = string.ascii_lowercase
        return ''.join(
                random.choice(allow_characters) for i in range(length))


    def long_text(self):
        return "Lorem Ipsum is simply dummy text of the printing and " \
               "typesetting industry. Lorem Ipsum has been the industry's " \
               "standard dummy text ever since the 1500s, when an " \
               "unknown printer took a galley of type and scrambled it " \
               "to make a type specimen book."

    def unique_str(self, len=None):
        return uuid.uuid4().hex[:len or 12].upper()

    def unique_id(self):
        return str(uuid.uuid4())

    def email(self):
        return '%s_%s@teko.com' % (
            fake.name().replace(' ', '_'),
            self.unique_str()
        )

    def slugify(self):
        return self.text().replace(' ', '-').lower()

    def datetime(self, min_year=1970, max_year=None, is_unix=False,
                 format=None, is_string=True):
        max_year = max_year or datetime.datetime.now().year
        start = datetime.datetime(min_year, 1, 1, 0, 0, 0)
        years = max_year - min_year + 1
        end = start + datetime.timedelta(days=365 * years)
        random_datetime = start + (end - start) * random.random()

        if is_unix:
            return int(time.mktime(random_datetime.timetuple()))

        if is_string:
            return random_datetime.strftime(format or "%m/%d/%Y %H:%M:%S")
        return random_datetime

    def choice(self, data):
        return random.choice(data)

    def url(self):
        return 'https://{}.{}'.format(self.text(), self.text())


fake = Faker()
fake.add_provider(Provider)
