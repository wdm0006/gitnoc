"""Analytics cache entries must be isolated per input and per profile.

Flask-Cache treats a literal ``key_prefix`` as the whole cache key, so the four
metrics services used to share one entry each: every ``repo_name`` collided on
``metrics_repo_details_``, and none of the keys mentioned the active profile.
These tests drive the real service functions through GitNOC's own caching
adapter (``services.analytics_cache``), standing in only for the Flask-Cache
backend itself.
"""
import datetime
import functools

import pytest

from gitnoc.services import analytics_cache
from gitnoc.services import metrics as metrics_service


PROFILE = {
    "profile_name": "a", "current_profile": True, "project_dir": "/tmp/code",
    "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main",
}


class RecordingCache:
    """Flask-Cache stand-in with the same literal-key semantics.

    ``cached`` uses ``key_prefix`` verbatim as the cache key (calling it first
    if it is a callable) and never mixes in the wrapped function's arguments --
    exactly what the real 0.13 implementation does.
    """

    def __init__(self):
        self.entries = {}
        self.calls = []

    def cached(self, timeout=None, key_prefix='view/%s'):
        def decorator(fn):
            @functools.wraps(fn)
            def decorated(*args, **kwargs):
                key = key_prefix() if callable(key_prefix) else key_prefix
                self.calls.append((key, timeout))
                if key not in self.entries:
                    self.entries[key] = fn(*args, **kwargs)
                return self.entries[key]
            return decorated
        return decorator


# --- minimal git-pandas fakes ----------------------------------------------

class _Values:
    def __init__(self, rows):
        self.rows = rows

    def tolist(self):
        return self.rows


class _Grouped:
    def __init__(self, rows):
        self.values = _Values(rows)

    def agg(self, *args, **kwargs):
        return self

    def reset_index(self, *args, **kwargs):
        return self

    def sort_values(self, *args, **kwargs):
        return self


class _Column:
    def __init__(self, total):
        self.total = total

    def sum(self):
        return self.total


class _HistoryFrame:
    def __init__(self, label):
        self.label = label

    def groupby(self, columns):
        return _Grouped([(self.label, 1)])

    def __getitem__(self, key):
        return _Column(1)


class _RowFrame:
    """Rows addressed as ``df.loc[idx, column]``, as pandas allows."""

    def __init__(self, rows):
        self.rows = rows

    @property
    def shape(self):
        return (len(self.rows), 0)

    @property
    def loc(self):
        return self

    def __getitem__(self, key):
        idx, column = key
        return self.rows[idx][column]

    def reset_index(self, *args, **kwargs):
        return self

    def sort_values(self, *args, **kwargs):
        return self


class _Repo:
    def __init__(self, name):
        self.name = name

    def _repo_name(self):
        return self.name

    def file_detail(self, extensions=None, ignore_dir=None):
        return _RowFrame([{
            'file': '%s.py' % self.name,
            'loc': 10,
            'file_owner': self.name,
            'ext': 'py',
            'last_edit_date': datetime.datetime(2024, 1, 1, 12, 0),
        }])


class FakeProjectDirectory:
    """Returns per-repository results so a key collision changes the output."""

    def __init__(self, working_dir=None, cache_backend=None):
        self.repos = [_Repo('api'), _Repo('web')]

    def commit_history(self, **kwargs):
        return _HistoryFrame('alice')

    def punchcard(self, **kwargs):
        return _RowFrame([{'day_of_week': 1, 'hour_of_day': 9, 'net': 3}])


@pytest.fixture
def cache_env(settings_env, monkeypatch):
    """Real services, recording cache backend, fake git-pandas."""
    settings_env.write([dict(PROFILE)])
    recorder = RecordingCache()
    monkeypatch.setattr(analytics_cache, "cache", recorder)
    monkeypatch.setattr(metrics_service, "ProjectDirectory", FakeProjectDirectory)
    return recorder


def keys_for(settings_env, profile):
    """Cache keys of all four analytics functions under ``profile``."""
    settings_env.write([profile])
    return {
        'leaderboard': metrics_service.week_leader_board.cache_key(n=5),
        'punchcard': metrics_service.get_punchcard.cache_key('/tmp/code', ['py'], ['vendor'], 'main'),
        'repo_details': metrics_service.get_repo_details.cache_key('api'),
        'repo_names': metrics_service.get_repo_names.cache_key(),
    }


# --- keys distinguish the request ------------------------------------------

def test_repo_details_keys_differ_per_repository(settings_env):
    settings_env.write([dict(PROFILE)])

    assert (metrics_service.get_repo_details.cache_key('api')
            != metrics_service.get_repo_details.cache_key('web'))


def test_leader_board_keys_differ_per_n(settings_env):
    settings_env.write([dict(PROFILE)])

    assert (metrics_service.week_leader_board.cache_key(n=5)
            != metrics_service.week_leader_board.cache_key(n=10))


def test_each_function_has_its_own_key_space(settings_env):
    keys = keys_for(settings_env, dict(PROFILE))

    assert len(set(keys.values())) == len(keys)


# --- keys distinguish the active configuration ------------------------------

@pytest.mark.parametrize("field, value", [
    ("profile_name", "other"),
    ("project_dir", "/tmp/other"),
    ("extensions", ["js"]),
    ("ignore_dir", ["node_modules"]),
    ("branch", "master"),
])
def test_all_keys_change_with_the_active_settings(settings_env, field, value):
    baseline = keys_for(settings_env, dict(PROFILE))

    changed = keys_for(settings_env, dict(PROFILE, **{field: value}))

    for name in baseline:
        assert baseline[name] != changed[name], name


# --- identical inputs stay stable -------------------------------------------

def test_identical_inputs_and_settings_produce_the_same_key(settings_env):
    assert keys_for(settings_env, dict(PROFILE)) == keys_for(settings_env, dict(PROFILE))


def test_keys_are_stable_across_normalized_equivalents(settings_env):
    """``get_settings`` turns ``None`` lists into ``[]``; keys follow the normalized value."""
    empty = dict(PROFILE, extensions=[], ignore_dir=[])

    assert keys_for(settings_env, empty) == keys_for(settings_env, dict(PROFILE, extensions=None, ignore_dir=None))


def test_positional_and_keyword_calls_share_a_key(settings_env):
    settings_env.write([dict(PROFILE)])

    assert (metrics_service.get_punchcard.cache_key('/tmp/code', ['py'], ['vendor'])
            == metrics_service.get_punchcard.cache_key(project_dir='/tmp/code', extensions=['py'],
                                                       ignore_dir=['vendor'], branch='master'))


# --- end-to-end through the caching adapter ---------------------------------

def test_repo_details_are_not_served_from_another_repository(cache_env):
    api = metrics_service.get_repo_details('api')
    web = metrics_service.get_repo_details('web')

    assert [row['file_name'] for row in api] == ['api.py']
    assert [row['file_name'] for row in web] == ['web.py']


def test_repeated_calls_hit_the_same_entry(cache_env):
    first = metrics_service.get_repo_details('api')
    second = metrics_service.get_repo_details('api')

    assert first is second
    assert len(cache_env.entries) == 1


def test_settings_change_invalidates_cached_repo_details(cache_env, settings_env):
    before = metrics_service.get_repo_details('api')
    settings_env.write([dict(PROFILE, branch="master")])

    after = metrics_service.get_repo_details('api')

    assert before is not after
    assert len(cache_env.entries) == 2


def test_every_analytics_function_keeps_the_600_second_ttl(cache_env):
    metrics_service.week_leader_board(n=5)
    metrics_service.get_punchcard('/tmp/code', ['py'], ['vendor'], 'main')
    metrics_service.get_repo_details('api')
    metrics_service.get_repo_names()

    assert len(cache_env.calls) == 4
    assert {timeout for _, timeout in cache_env.calls} == {600}


def test_cached_functions_keep_their_output_shape(cache_env):
    assert metrics_service.get_repo_names() == ['api', 'web']
    assert metrics_service.get_punchcard('/tmp/code', ['py'], ['vendor'], 'main') == [[1, 9, 3]]
    assert metrics_service.week_leader_board(n=5)['top_committers'] == [
        {'label': 'alice', 'net': 1, 'rank': 1},
    ]
