#!/usr/bin/env python
# -*- coding: utf-8 -*-
import code
import os
import sys

import click
import redis
from rq import Worker

from gitnoc.app import create_app

if 'server-prod' in sys.argv:
    app = create_app('prod')
else:
    app = create_app('dev')

HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')


def _make_context():
    """Return context dict for a shell session so you can access
    app, db, and the User model by default.
    """
    return {'app': app}


def _work(settings):
    connection = redis.from_url(settings.REDIS_URL)
    worker = Worker(settings.QUEUES, connection=connection)
    worker.work()


@click.group()
def manager():
    """Management commands for GitNOC."""


@manager.command('runworker')
def runworker():
    """Run an rq worker against the docker redis."""
    from gitnoc.settings import DockerConfig as settings
    _work(settings)


@manager.command('runworker_dev')
def runworker_dev():
    """Run an rq worker against the local redis."""
    from gitnoc.settings import LocalDevConfig as settings
    _work(settings)


@manager.command('server-dev')
def server_dev():
    """Run the development server on port 5050."""
    app.run(port=5050, threaded=True)


@manager.command('server-prod')
def server_prod():
    """Run the server on 0.0.0.0:5050 with the docker config."""
    app.run(host='0.0.0.0', port=5050, threaded=True)


@manager.command('shell')
def shell():
    """Start an interactive shell with the app in scope."""
    context = _make_context()
    with app.app_context():
        code.interact(local=context)


@manager.command('urls')
def urls():
    """Print the routes registered on the app."""
    rules = sorted(app.url_map.iter_rules(), key=lambda rule: rule.rule)
    rows = [(rule.rule, rule.endpoint, ','.join(sorted(rule.methods))) for rule in rules]
    headers = ('Rule', 'Endpoint', 'Methods')
    widths = [max(len(row[i]) for row in rows + [headers]) for i in range(3)]
    template = '  '.join('{:<%d}' % width for width in widths)
    click.echo(template.format(*headers).rstrip())
    click.echo('  '.join('-' * width for width in widths))
    for row in rows:
        click.echo(template.format(*row).rstrip())


if __name__ == '__main__':
    manager()
