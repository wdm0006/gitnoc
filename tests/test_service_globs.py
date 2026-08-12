"""Every analytics service must hand git-pandas the expanded ignore globs.

Same recorder pattern as ``test_service_branch.py``: stub each module's
``ProjectDirectory`` with a fake that captures the keyword arguments, drive the
real service functions, and assert on the glob lists git-pandas would receive.
"""
from gitnoc.services import cumulative_blame as cumulative_blame_service
from gitnoc.services import artifact_paths
from gitnoc.services import file_change_rates as file_change_rates_service
from gitnoc.services import metrics as metrics_service

PROFILE = {
    "profile_name": "a",
    "current_profile": True,
    "project_dir": "/tmp/code",
    "extensions": ["py"],
    "ignore_dir": ["tests", "src/vendor", "a-b.py"],
    "branch": "main",
}

EXPECTED_IGNORE = [
    'tests/*', '*/tests/*', 'tests', '*/tests',
    'src/vendor/*', '*/src/vendor/*', 'src/vendor', '*/src/vendor',
    'a-b.py/*', '*/a-b.py/*', 'a-b.py', '*/a-b.py',
]


# --- minimal DataFrame-ish fake ---------------------------------------------

class _Column:
    def sum(self):
        return 0


class _Mask:
    def __invert__(self):
        return self


class _Index:
    def duplicated(self):
        return _Mask()


class _Values:
    def tolist(self):
        return []


class FakeFrame:
    shape = (0, 0)
    index = _Index()
    values = _Values()

    def groupby(self, *args, **kwargs):
        return self

    def agg(self, *args, **kwargs):
        return self

    def reset_index(self, *args, **kwargs):
        return self

    def sort_values(self, *args, **kwargs):
        return self

    def __getitem__(self, key):
        return _Column() if isinstance(key, str) else self

    def to_json(self, orient='columns', **kwargs):
        return "[]" if orient == 'records' else "{}"


def make_recorder():
    calls = []

    class FakeRepo:
        def _repo_name(self):
            return "api"

        def file_detail(self, include_globs=None, ignore_globs=None, rev="HEAD", committer=True):
            calls.append(("file_detail", {'include_globs': include_globs, 'ignore_globs': ignore_globs}))
            return FakeFrame()

    class FakeProjectDirectory:
        def __init__(self, working_dir=None, cache_backend=None):
            self.repos = [FakeRepo()]

        def _record(self, name, kwargs):
            calls.append((name, kwargs))
            return FakeFrame()

        def commit_history(self, **kwargs):
            return self._record("commit_history", kwargs)

        def punchcard(self, **kwargs):
            return self._record("punchcard", kwargs)

        def cumulative_blame(self, **kwargs):
            return self._record("cumulative_blame", kwargs)

        def file_change_rates(self, **kwargs):
            return self._record("file_change_rates", kwargs)

    return FakeProjectDirectory, calls


def globs_for(calls, method, key):
    return [kwargs[key] for name, kwargs in calls if name == method]


def _redirect_blame_output(base_dir, monkeypatch):
    """Keep ``cumulative_blame``'s artifact write inside the temp dir."""
    fake_file = base_dir / "gitnoc" / "services" / "cumulative_blame.py"
    (base_dir / "gitnoc" / "static" / "data").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(artifact_paths, "__file__", str(fake_file))


# --- the five analytics services --------------------------------------------

def test_week_leader_board_passes_expanded_ignore_globs(settings_env, monkeypatch):
    settings_env.write([PROFILE])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(metrics_service, "ProjectDirectory", fake_pd)

    metrics_service.week_leader_board(n=5)

    # The combined query and the per-extension query both get the full list.
    assert globs_for(calls, "commit_history", "ignore_globs") == [EXPECTED_IGNORE] * 2
    assert globs_for(calls, "commit_history", "include_globs") == [['*.py'], ['*.py']]


def test_punchcard_passes_expanded_ignore_globs(settings_env, monkeypatch):
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(metrics_service, "ProjectDirectory", fake_pd)

    metrics_service.get_punchcard("/tmp/code", ["py"], ["tests", "src/vendor", "a-b.py"])

    assert globs_for(calls, "punchcard", "ignore_globs") == [EXPECTED_IGNORE]
    assert globs_for(calls, "punchcard", "include_globs") == [['*.py']]


def test_cumulative_blame_passes_expanded_ignore_globs(settings_env, tmp_path, monkeypatch):
    settings_env.write([PROFILE])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", fake_pd)
    _redirect_blame_output(tmp_path, monkeypatch)

    cumulative_blame_service.cumulative_blame("committer", "cumulative_author_blame.json")

    assert globs_for(calls, "cumulative_blame", "ignore_globs") == [EXPECTED_IGNORE]
    assert globs_for(calls, "cumulative_blame", "include_globs") == [['*.py']]


def test_file_change_rates_passes_expanded_ignore_globs(settings_env, monkeypatch):
    settings_env.write([PROFILE])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(file_change_rates_service, "ProjectDirectory", fake_pd)

    file_change_rates_service.get_file_change_rates()

    assert globs_for(calls, "file_change_rates", "ignore_globs") == [EXPECTED_IGNORE]
    assert globs_for(calls, "file_change_rates", "include_globs") == [['*.py']]


def test_repo_details_passes_expanded_ignore_globs(settings_env, monkeypatch):
    settings_env.write([PROFILE])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(metrics_service, "ProjectDirectory", fake_pd)

    metrics_service.get_repo_details("api")

    assert globs_for(calls, "file_detail", "ignore_globs") == [EXPECTED_IGNORE]
    assert globs_for(calls, "file_detail", "include_globs") == [['*.py']]
