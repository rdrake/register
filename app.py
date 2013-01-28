from register import app

from werkzeug import SharedDataMiddleware
import os

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
	"/": os.path.join(os.path.dirname(__file__), "static")
})

app.run(debug=True)
