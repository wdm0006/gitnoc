"""Deterministic Flask-Caching keys for the analytics services.

Flask-Caching treats a literal ``key_prefix`` as the *complete* cache key: it
never mixes in the decorated function's arguments, and a callable ``key_prefix``
is invoked with no arguments at all.  ``cached_analytics`` therefore builds the
key itself -- from the bound call arguments plus the analytics fields of the
active profile -- and hands Flask-Caching a callable that returns that
already-computed key.
"""
import functools
import hashlib
import inspect
import json

from gitnoc.app import cache
from .settings import get_settings

__author__ = 'willmcginnis'

#: Profile fields that change what an analytics call computes.
SETTINGS_KEYS = ('profile_name', 'project_dir', 'extensions', 'ignore_dir', 'branch')


def settings_fingerprint(settings):
    """Reduce a settings dict to the fields analytics results depend on."""
    return dict((key, settings.get(key)) for key in SETTINGS_KEYS)


def bind_arguments(fn, args, kwargs):
    """Normalize a call into a name -> value dict, defaults included.

    Binding through the signature means positionally and keyword-passed
    arguments produce the same key, and a name that is not a real parameter
    raises here rather than silently dropping out of the key.
    """
    bound = inspect.signature(fn).bind(*args, **kwargs)
    bound.apply_defaults()
    return dict(bound.arguments)


def make_cache_key(prefix, arguments, settings):
    """Build a stable cache key for ``arguments`` under ``settings``."""
    payload = json.dumps(
        {'arguments': arguments, 'settings': settings_fingerprint(settings)},
        sort_keys=True,
        default=repr,
    )
    return prefix + hashlib.sha256(payload.encode('utf-8')).hexdigest()


def cached_analytics(prefix, timeout=600):
    """Cache ``fn`` under a key that distinguishes its inputs and its profile."""
    def decorator(fn):
        def cache_key(*args, **kwargs):
            return make_cache_key(prefix, bind_arguments(fn, args, kwargs), get_settings())

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            key = cache_key(*args, **kwargs)
            return cache.cached(timeout=timeout, key_prefix=lambda: key)(fn)(*args, **kwargs)

        wrapper.cache_key = cache_key
        return wrapper
    return decorator
