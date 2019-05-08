from flask import current_app, g, redirect, request, session
from authlib.flask.client import OAuth
from lumavate_service_util import make_id, get_lumavate_request, LumavateRequest, SecurityAssertion
from lumavate_properties import Properties
from lumavate_exceptions import ApiException, AuthorizationException
from cryptography.fernet import Fernet
import os
import json
import time

class ServiceSecurityAssertion(SecurityAssertion):
  def load_rolemap(self):
    self._rolemap['readers'] = g.service_data.get('readRoles', [])

class Service():

  def properties(self, integration_cloud='ic', url_ref='auth-0'):
    c = Properties.ComponentPropertyType
    widget_props = []

    ################################
    # Authentication
    ################################

    widget_props.append(Properties.Property(
      'Auth0',
      'Authorization Settings',
      'readRoles',
      'Group Administration',
      'multiselect',
      options = ServiceSecurityAssertion().get_all_auth_groups(),
      default=[]))

    ################################
    # AUTH0 Application Settings
    ################################
    ht = '''
The Domain associated with the Auth0 Application used for authentication
    '''

    widget_props.append(Properties.Property(
      'Auth0',
      'Application Settings',
      'domain',
      'Application Domain',
      'text',
      help_text=ht,
      options={}))

    ht = '''
The Client ID associated with the Auth0 Application used for authentication
    '''

    widget_props.append(Properties.Property(
      'Auth0',
      'Application Settings',
      'clientId',
      'Client ID',
      'text',
      help_text=ht,
      options={}))

    ht = '''
The Client Secret associated with the Auth0 Application used for authentication
    '''

    widget_props.append(Properties.Property(
      'Auth0',
      'Application Settings',
      'clientSecret',
      'Client Secret',
      'text',
      help_text=ht,
      options={}))

    ################################
    # Session
    ################################
    ht = '''
The amount of time in seconds that a user can remain logged in to the experience
    '''
    widget_props.append(Properties.Property(
      'Advanced',
      'Session Settings',
      'sessionMaxDuration',
      'Session Max Duration (Seconds)',
      'numeric',
      default = 60 * 60 * 24 * 30,
      help_text=ht,
      options={'min': 0}))

    ht = '''
After successfully logging in, this setting will direct the user to the appropriate
page.  If unset the user will be sent to the home page.
    '''
    widget_props.append(Properties.Property(
      'Advanced',
      'Session Settings',
      'loginPageLink',
      'Login Page Link',
      'page-link',
      help_text=ht))

    widget_props.append(Properties.Property(
      'Advanced',
      'Session Settings',
      'errorPageLink',
      'Error Page Link',
      'page-link'))

    return [x.to_json() for x in widget_props]

  def auth_groups(self):
    groups = []
    for group in g.service_data.get('authGroups', []):
      groups.append({'name': group['componentData']['title']})

    return groups

  def get_max_session_duration(self):
    return g.service_data.get('sessionMaxDuration')

  def get_encryption_private_key(self):
    return os.getenv('ENCRYPTION_PRIVATE_KEY', 'yNokwIVf-z3zaYtqg6ywM2cmKUmIleUwzxLG8qz2k7Y=').encode('utf-8')

  def authorize_wrapper(self, func):
    try:
      return func()
    except ApiException as e:
      #Update current Session
      return func()

  def encrypt_session_info(self, sessionInfo):
    cipher_suite = Fernet(self.get_encryption_private_key())
    return {
      os.getenv('SERVICE_NAME', 'AUTH0'): cipher_suite.encrypt(json.dumps(sessionInfo).encode('utf-8')).decode()
    }

  def get_auth0_client(self):
    if ('OAuth' not in g):
      g.OAuth = OAuth(current_app).register(
        'auth0',
        client_id=g.service_data['clientId'],
        client_secret=g.service_data['clientSecret'],
        api_base_url=g.service_data['domain'],
        access_token_url=g.service_data['domain'] + '/oauth/token',
        authorize_url=g.service_data['domain'] + '/authorize',
        client_kwargs={
          'scope':'openid profile'
        },
      )

    return g.OAuth

  def login(self):
    auth0 = self.get_auth0_client()
    print('Client created successfully',flush=True)
    return auth0.authorize_redirect(redirect_uri='https://' + request.host + '/' + g.integration_cloud + '/' + g.widget_type  + '/callback', audience=g.service_data['domain'] + '/userinfo')

  def callback(self):
    print('Callback',flush=True)
    try:
      auth0 = self.get_auth0_client()
      auth0.authorize_access_token()
      resp = auth0.get('userinfo')
      userinfo = resp.json()

      session_info = {
        "jwt_payload": userinfo,
        "profile": {
          "user_id": userinfo['sub'],
          "name": userinfo['name'],
          "picture": userinfo['picture']
        }
      }

      user= {
        'email': userinfo['sub'],
        'session': g.token_data['session'],
        'sessionStart': time.time(),
        'userdata': session_info
      }

      get_lumavate_request().put('/pwa/v1/session',self.encrypt_session_info(user))

      if g.service_data.get('loginPageLink') is not None:
        url = g.service_data.get('loginPageLink', {}).get('url')
        if not url.startswith('http'):
          url = 'https://' + request.host + url
        return redirect(url, 302)
      else:
        return redirect('https://' + request.host, 302)

    except Exception as e:
      print('Parse Auth error: ' + str(e))
      if g.service_data.get('errorPageLink') is not None:
        url = g.service_data.get('errorPageLink', {}).get('url')
        if not url.startswith('http'):
          url = 'https://' + request.host + url
        return redirect(url, 302)
      else:
        return 'Auth0 Error (please log out of Auth0 and try again, or contact system administrator): ' + str(e)

  def status_data(self):
    data = g.session.get(os.getenv('SERVICE_NAME', 'AUTH0'))
    if data is None:
      raise AuthorizationException('No Session')

    data = data.encode('utf-8')
    cipher_suite = Fernet(self.get_encryption_private_key())
    userinfo = json.loads(cipher_suite.decrypt(data).decode())

    ens = userinfo.get('email')
    if ens is None:
      raise AuthorizationException('No User')

    if time.time() - userinfo.get('sessionStart', 0) > self.get_max_session_duration():
      raise AuthorizationException('Old Session')

    roles = []

    return {
        'user': ens + 'user',
        'roles': roles,
        'status': 'active',
        'additionalData': userinfo.get('userdata')
    }

  def status(self):
    return self.status_data()

  def show_status(self):
    return jsonify(self.status_data())

  def logout(self):
    sess_data = {
      os.getenv('SERVICE_NAME', 'AUTH0'): None
    }

    get_lumavate_request().put('/pwa/v1/session', sess_data)
    return {'status': 'Ok'}
