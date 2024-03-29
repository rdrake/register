from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.mail import Mail
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.storage import get_default_storage_class
from flask.ext.uploads import init

from flask_debugtoolbar import DebugToolbarExtension

import sys

import stripe

from .models import Guardian, Role, db

app = Flask(__name__)
app.config.from_pyfile("config.py")

db.app = app
db.init_app(app)

CONVENIENCE_FEE = 500

# Set to live keys by default.
STRIPE_KEYS = {
  "secret_key": "sk_076KMBjuzftnlqaTOHhsMfRRk8qhZ",
  "publishable_key": "pk_076K5dtDYTT6lRCvpC6HrIWbSeY3a"
}

if sys.platform == "darwin":
  app.debug = True

  STRIPE_KEYS = {
    "secret_key": "sk_076KrUmlyQWYeTysIbXuapSy7AWcX",
    "publishable_key": "pk_076KVxlFN6XEzWvaHaTfES34ccZ7E",
  }

stripe.api_key = STRIPE_KEYS["secret_key"]

mail = Mail(app)
Bootstrap(app)

user_datastore = SQLAlchemyUserDatastore(db, Guardian, Role)
security = Security(app, user_datastore)

storage = get_default_storage_class(app)
init(db, storage)

toolbar = DebugToolbarExtension(app)

from .views import home

#if __name__ == "__main__":
#  app.run(debug=True, port=9090)
