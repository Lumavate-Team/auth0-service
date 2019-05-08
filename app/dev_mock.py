from lumavate_properties import Properties, Components
from lumavate_service_util import LumavateMockRequest, set_lumavate_request_factory, DevMock
from lumavate_token import AuthToken
import json

class ServiceDevMock(DevMock):
  def get_auth_token(self):
    t = super().get_auth_token()
    t.auth_url = 'http://localhost:5002/'
    return t

  def get_property_data(self):
    sd = super().get_property_data()
    sd.set_property('clientId', 'yDDkN1RdItgNChZ3QPwO67NFiQzmt4jP')
    sd.set_property('clientSecret', 'RKSaihUso6dzcTLwst8qh9Wa5QzS94p0JFpzW73Sq28X2YmEYPdxDtODWSCi_ko2')
    sd.set_property('audience', 'https://dragonfly.lumavate-dev.com/app')
    sd.set_property('tokenUri', 'https://dragonfly-lumavate-dev.auth0.com/oauth/token')
    return sd

  def get_auth_data(self):
    return {
      'roles': [
        'Super Admin',
        'Admins'
      ],
      'status': 'active',
      'user': 'ic/magiclink|email|2'
    }
