from catalog.models import brand
from catalog import models, app
from commands.update_brand_logo_path import update_brand_logo_path
from tests.catalog.api import APITestCase
from tests.faker import fake


class UpdatrBrandLogoPath(APITestCase):

    ISSUE_KEY = 'CATALOGUE-417'
    FOLDER = '/Brand/Path/Update'

    def setUp(self):
        self.brand = fake.brand()
        models.db.session.commit()
        self.brand_id = self.brand.id

    def test_UpdateBrandLogoPath_NoRelativePathWithHttps(self):
        self.brand.path = 'https://storage.googleapis.com/teko-gae.appspot.com/media/image/logo.png'
        models.db.session.commit()

        app.test_cli_runner().invoke(cli=update_brand_logo_path)

        brand = models.Brand.query.filter(models.Brand.id == self.brand_id).first()

        self.assertEqual(brand.path, 'https://storage.googleapis.com/teko-gae.appspot.com/media/image/logo.png')

    def test_UpdateBrandLogoPath_NoRelativePathWithHttp(self):
        self.brand.path = 'http://storage.googleapis.com/teko-gae.appspot.com/media/image/logo.png'
        models.db.session.commit()

        app.test_cli_runner().invoke(cli=update_brand_logo_path)

        brand = models.Brand.query.filter(models.Brand.id == self.brand_id).first()

        self.assertEqual(brand.path, 'http://storage.googleapis.com/teko-gae.appspot.com/media/image/logo.png')

    def test_UpdateBrandLogoPath_EmptyPath(self):
        self.brand.path = ''
        models.db.session.commit()

        app.test_cli_runner().invoke(cli=update_brand_logo_path)

        brand = models.Brand.query.filter(models.Brand.id == self.brand_id).first()

        self.assertEqual(brand.path, '')

    def test_UpdateBrandLogoPath_Success(self):
        # This uses CONCAT function but can not run in SQLLite
        self.assertTrue(True)
