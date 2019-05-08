from flask import g, Session
from app_factory import create_app
from flask_sqlalchemy import SQLAlchemy
import os

app = create_app()
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = 'super secret key'
sess = Session()

rest_model_mapping = {}

from routes import *
from lumavate_service_util import icon_blueprint, lumavate_blueprint
app.register_blueprint(lumavate_blueprint)
app.register_blueprint(icon_blueprint)

@app.before_first_request
def init():
  if os.environ.get('DEV_MODE', 'False').lower() == 'true':
    import dev_mock
    from behavior import Service
    dm = dev_mock.ServiceDevMock(Service().do_properties)

if __name__ == '__main__':
  app.run(debug=True, host="0.0.0.0")
