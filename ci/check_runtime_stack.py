"""Assert the real dependency stack imports and the application composes.

The pytest suite stubs gitpandas, the cache extension, redis and numpy so it can
run without them, which means it stays green over a stack that cannot import at
all.  This script runs against the unstubbed ``requirements.txt`` and is what CI
uses to catch a regression in any of the four imports that used to die on a
current resolution (flask-caching, flask-script, flask-wtf, ``rq.Connection``).

Needs a reachable redis: ``gitnoc.extensions`` builds a git-pandas
``RedisDFCache`` at import time, and that syncs its key list immediately.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

EXPECTED_ROUTES = {
    '/',
    '/punchcard_data',
    '/repo_details/<repo_name>/',
    '/blame',
    '/cumulative_author_blame',
    '/cumulative_author_blame_data',
    '/cumulative_project_blame',
    '/cumulative_project_blame_data',
    '/risk',
    '/file_change_rates',
    '/settings',
    '/profile',
    '/ignore_file/<path:file_name>/',
}

EXPECTED_COMMANDS = {'server-dev', 'server-prod', 'runworker', 'runworker_dev', 'shell', 'urls'}


def main():
    # The imports that died on a current resolution before the stack swap.
    import click  # noqa: F401
    import flask_caching  # noqa: F401
    from flask_wtf import FlaskForm
    from rq import Queue, Worker  # noqa: F401

    from gitnoc.app import create_app
    app = create_app('dev')

    missing = EXPECTED_ROUTES - {rule.rule for rule in app.url_map.iter_rules()}
    if missing:
        raise AssertionError('missing routes: %s' % sorted(missing))

    # Prove the configured cache backend is a working redis client, not just an
    # importable name: CACHE_TYPE has to be a spelling Flask-Caching 2.x knows.
    from gitnoc.extensions import cache
    with app.app_context():
        cache.set('gitnoc_ci_probe', 'ok', timeout=30)
        if cache.get('gitnoc_ci_probe') != 'ok':
            raise AssertionError('the configured cache backend did not round-trip a value')

    from gitnoc.forms.public import SettingsForm
    if not issubclass(SettingsForm, FlaskForm):
        raise AssertionError('SettingsForm must subclass FlaskForm, not plain wtforms.Form')
    if not hasattr(SettingsForm, 'validate_on_submit'):
        raise AssertionError('SettingsForm lost validate_on_submit')

    import manage
    missing = EXPECTED_COMMANDS - set(manage.manager.commands)
    if missing:
        raise AssertionError('missing manage.py commands: %s' % sorted(missing))

    print('OK: app composed, %d routes, %d commands' % (
        len(EXPECTED_ROUTES), len(manage.manager.commands)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
