import os
from flask import Flask, render_template
from gitnoc.extensions import (
    gp_cache,
    cache
)
from redis import Redis
from rq import Queue
from gitnoc.assets import assets
from gitnoc.views.admin import blueprint as admin_blueprint
from gitnoc.views.blame import blueprint as blame_blueprint
from gitnoc.views.metrics import blueprint as metrics_blueprint
from gitnoc.views.risk import blueprint as risk_blueprint
from gitnoc.settings import DockerConfig, LocalDevConfig

q = None


def create_app(env='dev'):
    app = Flask(__name__)
    app.secret_key = 'CHANGEME'

    directory = str(os.path.dirname(os.path.abspath(__file__))) + os.sep + 'static' + os.sep + 'data'
    if not os.path.exists(directory):
        os.makedirs(directory)

    if env == 'dev':
        app.config.from_object(LocalDevConfig)
    else:
        app.config.from_object(DockerConfig)

    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)

    return app


def register_extensions(app):
    global q  #: sorry.
    q = Queue(connection=Redis(host=app.config['CACHE_REDIS_HOST']))
    cache.init_app(app)
    assets.init_app(app)

    return None


def register_blueprints(app):
    app.register_blueprint(admin_blueprint)
    app.register_blueprint(blame_blueprint)
    app.register_blueprint(metrics_blueprint)
    app.register_blueprint(risk_blueprint)


def register_errorhandlers(app):
    def render_error(error):
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template("{0}.html".format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None
