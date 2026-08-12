"""Cumulative-blame artifacts must be published atomically.

The worker used to dump straight into ``open(path, 'w')``, which truncates the
live artifact before serialization runs.  The blame data routes read that same
path and only handle a missing file, so a request landing mid-refresh could see
an empty/partial document, and a failed dump destroyed the last good result.

``_write_artifact`` serializes into a sibling temp file and only then replaces
the live artifact, so readers see either the old bytes or the new ones.
"""
import json
import os

import pytest

from gitnoc.services import cumulative_blame as cumulative_blame_service


# --- minimal DataFrame-ish fake -------------------------------------------

class _Mask:
    def __invert__(self):
        return self


class _Index:
    def duplicated(self):
        return _Mask()


class FakeFrame:
    """Returns a fixed cumulative-blame payload so the artifact has real values."""

    index = _Index()

    def __getitem__(self, key):
        return self

    def to_json(self, *args, **kwargs):
        return json.dumps({"alice": {"1000": 5, "2000": 7}})


class FakeProjectDirectory:
    def __init__(self, working_dir=None, cache_backend=None):
        pass

    def cumulative_blame(self, **kwargs):
        return FakeFrame()


EXPECTED_SERIES = [{"key": "alice", "values": [[1000, 5], [2000, 7]]}]


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Redirect the service's artifact directory into ``tmp_path``.

    ``_artifact_path`` derives ``<pkg>/static/data/<file>`` from the module's own
    ``__file__``, so pointing that at a fake two-levels-deep location moves every
    read and write into the throwaway tree.
    """
    fake_file = tmp_path / "gitnoc" / "services" / "cumulative_blame.py"
    directory = tmp_path / "gitnoc" / "static" / "data"
    directory.mkdir(parents=True)
    monkeypatch.setattr(cumulative_blame_service, "__file__", str(fake_file))
    return directory


def _profile(settings_env, name="a"):
    settings_env.write([
        {"profile_name": name, "current_profile": True,
         "project_dir": "/tmp/code", "extensions": ["py"], "ignore_dir": ["vendor"],
         "branch": "main"},
    ])


def test_refresh_replaces_artifact_with_new_series(settings_env, data_dir, monkeypatch):
    _profile(settings_env)
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", FakeProjectDirectory)
    artifact = data_dir / "a_cumulative_author_blame.json"
    artifact.write_text(json.dumps([{"key": "stale", "values": [[1, 1]]}]))

    cumulative_blame_service.cumulative_blame("committer", "cumulative_author_blame.json")

    assert json.loads(artifact.read_text()) == EXPECTED_SERIES


def test_refresh_writes_artifact_when_none_exists(settings_env, data_dir, monkeypatch):
    _profile(settings_env)
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", FakeProjectDirectory)

    cumulative_blame_service.cumulative_blame("committer", "cumulative_project_blame.json")

    artifact = data_dir / "a_cumulative_project_blame.json"
    assert json.loads(artifact.read_text()) == EXPECTED_SERIES


def test_failed_serialization_leaves_previous_artifact_byte_for_byte(data_dir):
    """The assertion that actually catches the truncating write.

    ``json.dump`` emits the leading chunks before it reaches the unserializable
    value, so writing has begun by the time it raises.  Dumping into the live
    path would leave those partial bytes (or nothing) behind.
    """
    artifact = data_dir / "a_cumulative_author_blame.json"
    previous = json.dumps(EXPECTED_SERIES, indent=4)
    artifact.write_text(previous)

    # A set is not JSON-serializable; the preceding key is written first.
    doomed = [{"key": "alice", "values": [[1000, 5]]}, {"key": "bob", "values": {1, 2}}]
    with pytest.raises(TypeError):
        cumulative_blame_service._write_artifact("a_cumulative_author_blame.json", doomed)

    assert artifact.read_text() == previous


def test_failed_serialization_leaves_no_temporary_file(data_dir):
    artifact = data_dir / "a_cumulative_author_blame.json"
    artifact.write_text("[]")

    with pytest.raises(TypeError):
        cumulative_blame_service._write_artifact("a_cumulative_author_blame.json", {1, 2})

    assert os.listdir(str(data_dir)) == ["a_cumulative_author_blame.json"]
