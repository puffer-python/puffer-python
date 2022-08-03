from unittest import TestCase
from mock import patch
import requests
from catalog.services import provider as provider_srv


class GetProviderTestCase(TestCase):
    def test_get_provider_by_id(self):
        resp = requests.Response()
        resp.status_code = 200
        resp._content = b'''
        {
          "code": "SA001D",
          "message": "API has no specific code for this case",
          "result": {
            "provider": {
              "isActive": 1,
              "slogan": "ssv",
              "updatedAt": "2020-07-29 04:55:12",
              "displayName": "provider 1",
              "name": "nha cung cap 1",
              "id": 100000,
              "isOwner": 0,
              "logo": "https://storage.googleapis.com/teko-gae.appspot.com/media/image/2020/7/29/20200729_c95da8c7-35d9-46d6-9d47-3c0e3f62e0b6.png",
              "sellerID": 2,
              "code": "NCCA",
              "createdAt": "2020-07-29 04:55:12"
            }
          }
        }
        '''
        with patch('requests.get') as mock_resp:
            mock_resp.return_value = resp
            provider = provider_srv.get_provider_by_id(6969)
            assert isinstance(provider, dict)
