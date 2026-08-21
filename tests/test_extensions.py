import importlib.util
import sys
import types
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ('environment', 'expected_host', 'expected_port'),
    [
        ({}, 'localhost', 6379),
        ({'GITNOC_REDIS_HOST': 'redis', 'GITNOC_REDIS_PORT': '6380'}, 'redis', 6380),
    ],
)
def test_gitpandas_cache_redis_endpoint(monkeypatch, environment, expected_host, expected_port):
    captured = {}

    class FakeRedisDFCache:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.delenv('GITNOC_REDIS_HOST', raising=False)
    monkeypatch.delenv('GITNOC_REDIS_PORT', raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    gitpandas = types.ModuleType('gitpandas')
    gitpandas.__path__ = []
    gitpandas_cache = types.ModuleType('gitpandas.cache')
    gitpandas_cache.RedisDFCache = FakeRedisDFCache
    flask_caching = types.ModuleType('flask_caching')
    flask_caching.Cache = type('FakeCache', (), {})
    monkeypatch.setitem(sys.modules, 'gitpandas', gitpandas)
    monkeypatch.setitem(sys.modules, 'gitpandas.cache', gitpandas_cache)
    monkeypatch.setitem(sys.modules, 'flask_caching', flask_caching)

    extension_path = Path(__file__).parents[1] / 'gitnoc' / 'extensions.py'
    spec = importlib.util.spec_from_file_location('_gitnoc_extensions_test', extension_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert captured['host'] == expected_host
    assert captured['port'] == expected_port
    assert captured['db'] == 3
