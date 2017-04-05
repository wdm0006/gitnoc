#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask_script import Manager, Shell, Server
from flask_script.commands import Clean, ShowUrls
import redis
from rq import Connection, Worker
from gitnoc.app import create_app
import sys

if 'server-prod' in sys.argv:
    app = create_app('prod')
else:
    app = create_app('dev')

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

manager = Manager(app)


def _make_context():
    """Return context dict for a shell session so you can access
    app, db, and the User model by default.
    """
    return {'app': app}


@manager.command
def runworker():
    from gitnoc.settings import DockerConfig as settings
    redis_connection = redis.from_url(settings.REDIS_URL)
    with Connection(redis_connection):
        worker = Worker(settings.QUEUES)
        worker.work()


@manager.command
def runworker_dev():
    from gitnoc.settings import LocalDevConfig as settings
    redis_connection = redis.from_url(settings.REDIS_URL)
    with Connection(redis_connection):
        worker = Worker(settings.QUEUES)
        worker.work()

manager.add_command('server-dev', Server(port=5050, threaded=True))
manager.add_command('server-prod', Server(host='0.0.0.0', port=5050, threaded=True))
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command("urls", ShowUrls())
manager.add_command("clean", Clean())

if __name__ == '__main__':
    manager.run()
