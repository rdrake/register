import os.path

# Flask stuff.
DEBUG = True
SECRET_KEY = "d/)~6{d]c{N^Yo,}ETSMTxv8-z[yuuY/88 eK[[1Nwz=3"

# The database is very trusting.
SQLALCHEMY_DATABASE_URI = "postgresql://localhost/register"

# Use gmail's SMTP server.
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USE_SSL = False
MAIL_USE_TLS = True
MAIL_USERNAME = "no-reply@nascsoccer.org"
MAIL_PASSWORD = "eDGar*5Y1"
DEFAULT_MAIL_SENDER = "no-reply@nascsoccer.org"

# Setup flask-security.
SECURITY_PASSWORD_HASH = "bcrypt" #"pbkdf2_sha512"
SECURITY_PASSWORD_SALT = "A!T|=1WGR`UX4?jX|:qgEa{})[(T8Y6#-|zz+kTsR6c2J2/5<%-M#zm,V=TXx88I"
SECURITY_EMAIL_SENDER = "no-reply@nascsoccer.org"
SECURITY_CONFIRMABLE = True

# Setup flask-bootstrap.  For some reason it defaults to "1" which is 404.
BOOTSTRAP_JQUERY_VERSION = "1.8.3"
BOOTSTRAP_FONTAWESOME = True

# flask-uploads
DEFAULT_FILE_STORAGE = "filesystem"
UPLOADS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static", "img")
FILE_SYSTEM_STORAGE_FILE_VIEW = "static"
