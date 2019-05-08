from lumavate_service_util import lumavate_route, SecurityType, RequestType
from flask import request, render_template, g, redirect
from behavior import Service

@lumavate_route('/', ['GET'], RequestType.page, [SecurityType.jwt])
def root():
  return render_template('home.html', logo='/{}/{}/discover/icons/microservice.png'.format(g.integration_cloud, g.widget_type))

@lumavate_route('/discover/properties', ['GET'], RequestType.system, [SecurityType.jwt])
def properties():
  return Service().properties()

@lumavate_route('/login', ['GET'], RequestType.page, [SecurityType.jwt])
def login():
  return Service().login()

@lumavate_route('/callback', ['GET'], RequestType.page, [SecurityType.jwt])
def callback():
  return Service().callback()

@lumavate_route('/status', ['POST', 'GET'], RequestType.api, [SecurityType.jwt])
def status():
  return Service().status()

@lumavate_route('/showstatus', ['GET'], RequestType.page, [SecurityType.jwt])
def show_status():
  return Service().show_status()

