"""Guard the Redis connection URLs compiled into ``gitnoc/settings.py``.

``manage.py runworker`` / ``runworker_dev`` hand ``REDIS_URL`` straight to
``redis.from_url``, which only accepts the ``redis``, ``rediss`` and ``unix``
schemes.  redis-py is not a CI dependency, so the check is done with
``urllib.parse`` instead of by connecting.
"""
import pytest
from urllib.parse import urlsplit

from gitnoc.settings import DockerConfig, LocalDevConfig

# The schemes redis-py's ``from_url`` accepts; anything else raises ValueError.
REDIS_SCHEMES = ('redis', 'rediss', 'unix')

CONFIGS = [
    ('LocalDevConfig', LocalDevConfig),
    ('DockerConfig', DockerConfig),
]


@pytest.mark.parametrize('name, config', CONFIGS)
def test_redis_url_uses_a_scheme_redis_py_accepts(name, config):
    scheme = urlsplit(config.REDIS_URL).scheme
    assert scheme in REDIS_SCHEMES, (
        '%s.REDIS_URL is %r; redis.from_url only accepts %s'
        % (name, config.REDIS_URL, ', '.join(s + '://' for s in REDIS_SCHEMES))
    )


@pytest.mark.parametrize('name, config', CONFIGS)
def test_redis_url_names_database_zero(name, config):
    # gitnoc.app enqueues on Redis(host=...), i.e. redis-py's default database
    # 0, so the worker's URL has to name the same database or the jobs the web
    # process enqueues are never consumed.
    assert urlsplit(config.REDIS_URL).path == '/0', (
        '%s.REDIS_URL is %r; it must name database 0 to share the queue with '
        'the enqueuing web process' % (name, config.REDIS_URL)
    )
