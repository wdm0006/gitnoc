"""The configured profile branch must reach every branch-aware git-pandas call.

These tests stub ``gitpandas.ProjectDirectory`` with a recorder that captures
the ``branch`` keyword handed to ``commit_history``, ``punchcard`` and
``cumulative_blame``, then drive the real service functions and assert the
active profile's branch (not a hardcoded ``master``) is what git-pandas sees.

The heavy pandas/numpy machinery is stubbed out in ``conftest.py``; the fake
frames below return just enough surface for each service to run to completion.
"""
from gitnoc.services import metrics as metrics_service
from gitnoc.services import cumulative_blame as cumulative_blame_service


# --- minimal DataFrame-ish fakes -------------------------------------------

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
    """Enough of the pandas surface for the three services to complete."""

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
        # ch['net'] -> a column with .sum(); cb[~mask] -> the frame itself.
        return _Column() if isinstance(key, str) else self

    def to_json(self, *args, **kwargs):
        return "{}"


def make_recorder():
    calls = []

    class FakeProjectDirectory:
        def __init__(self, working_dir=None, cache_backend=None):
            pass

        def commit_history(self, branch=None, **kwargs):
            calls.append(("commit_history", branch))
            return FakeFrame()

        def punchcard(self, branch=None, **kwargs):
            calls.append(("punchcard", branch))
            return FakeFrame()

        def cumulative_blame(self, branch=None, **kwargs):
            calls.append(("cumulative_blame", branch))
            return FakeFrame()

    return FakeProjectDirectory, calls


def branches_for(calls, method):
    return [branch for name, branch in calls if name == method]


def test_week_leader_board_uses_configured_branch(settings_env, monkeypatch):
    settings_env.write([
        {"profile_name": "a", "current_profile": True,
         "project_dir": "/tmp/code", "extensions": ["py"], "ignore_dir": ["vendor"],
         "branch": "main"},
    ])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(metrics_service, "ProjectDirectory", fake_pd)

    metrics_service.week_leader_board(n=5)

    # Both the leaderboard call and the per-extension history call use the branch.
    assert branches_for(calls, "commit_history") == ["main", "main"]


def test_punchcard_uses_passed_branch(settings_env, monkeypatch):
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(metrics_service, "ProjectDirectory", fake_pd)

    metrics_service.get_punchcard("/tmp/code", ["py"], ["vendor"], branch="develop")

    assert branches_for(calls, "punchcard") == ["develop"]


def test_punchcard_defaults_to_master(settings_env, monkeypatch):
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(metrics_service, "ProjectDirectory", fake_pd)

    metrics_service.get_punchcard("/tmp/code", ["py"], ["vendor"])

    assert branches_for(calls, "punchcard") == ["master"]


def _redirect_blame_output(cumulative_module, base_dir, monkeypatch):
    """Point the service's ``__file__`` (and thus its output dir) into tmp_path.

    ``cumulative_blame`` derives its output directory from its own ``__file__``
    and writes ``<dir>/static/data/<file>``; the ``open(...)`` argument creates
    that file even if ``json.dump`` is a no-op, so we redirect the whole tree
    into the throwaway temp dir instead of polluting the repo.
    """
    fake_file = base_dir / "gitnoc" / "services" / "cumulative_blame.py"
    (base_dir / "gitnoc" / "static" / "data").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(cumulative_module, "__file__", str(fake_file))


def test_cumulative_blame_uses_configured_branch(settings_env, tmp_path, monkeypatch):
    settings_env.write([
        {"profile_name": "a", "current_profile": True,
         "project_dir": "/tmp/code", "extensions": ["py"], "ignore_dir": ["vendor"],
         "branch": "main"},
    ])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", fake_pd)
    _redirect_blame_output(cumulative_blame_service, tmp_path, monkeypatch)

    cumulative_blame_service.cumulative_blame("committer", "cumulative_author_blame.json")

    assert branches_for(calls, "cumulative_blame") == ["main"]


def test_cumulative_blame_missing_branch_falls_back_to_master(settings_env, tmp_path, monkeypatch):
    settings_env.write([
        {"profile_name": "legacy", "current_profile": True,
         "project_dir": "/tmp/code", "extensions": ["py"], "ignore_dir": ["vendor"]},
    ])
    fake_pd, calls = make_recorder()
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", fake_pd)
    _redirect_blame_output(cumulative_blame_service, tmp_path, monkeypatch)

    cumulative_blame_service.cumulative_blame("committer", "cumulative_author_blame.json")

    assert branches_for(calls, "cumulative_blame") == ["master"]
