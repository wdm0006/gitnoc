import os
from flask import Flask
from gitnoc.extensions import (
    q,
    cache
)
from gitnoc.assets import assets
from gitnoc.views.admin import blueprint as admin_blueprint
from gitnoc.views.blame import blueprint as blame_blueprint
from gitnoc.views.metrics import blueprint as metrics_blueprint
from gitnoc.views.risk import blueprint as risk_blueprint


def create_app():
    app = Flask(__name__)
    app.secret_key = 'CHANGEME'

    directory = str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data'
    if not os.path.exists(directory):
        os.makedirs(directory)

    app.config['ASSETS_DEBUG'] = True
    app.config['DEBUG'] = True
    register_extensions(app)
    register_blueprints(app)

    return app


def register_extensions(app):
    cache.init_app(app)
    assets.init_app(app)

    return None


def register_blueprints(app):
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(blame_blueprint)
    app.register_blueprint(metrics_blueprint)
    app.register_blueprint(risk_blueprint)
