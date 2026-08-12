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

from gitnoc.services import artifact_paths
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

    ``artifact_paths`` derives ``<pkg>/static/data/<file>`` from its own module
    ``__file__``, so pointing that at a fake two-levels-deep location moves every
    read and write into the throwaway tree.
    """
    fake_file = tmp_path / "gitnoc" / "services" / "artifact_paths.py"
    directory = tmp_path / "gitnoc" / "static" / "data"
    directory.mkdir(parents=True)
    monkeypatch.setattr(artifact_paths, "__file__", str(fake_file))
    return directory


def _artifact(file_stub, profile="a"):
    """The live artifact path for ``profile``, as the worker and routes derive it."""
    return artifact_paths.cumulative_blame_artifact_path(profile, file_stub)


def _profile(settings_env, name="a"):
    settings_env.write([
        {"profile_name": name, "current_profile": True,
         "project_dir": "/tmp/code", "extensions": ["py"], "ignore_dir": ["vendor"],
         "branch": "main"},
    ])


def test_refresh_replaces_artifact_with_new_series(settings_env, data_dir, monkeypatch):
    _profile(settings_env)
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", FakeProjectDirectory)
    artifact = _artifact("cumulative_author_blame.json")
    with open(artifact, "w") as handle:
        json.dump([{"key": "stale", "values": [[1, 1]]}], handle)

    cumulative_blame_service.cumulative_blame("committer", "cumulative_author_blame.json")

    with open(artifact) as handle:
        assert json.load(handle) == EXPECTED_SERIES


def test_refresh_writes_artifact_when_none_exists(settings_env, data_dir, monkeypatch):
    _profile(settings_env)
    monkeypatch.setattr(cumulative_blame_service, "ProjectDirectory", FakeProjectDirectory)

    cumulative_blame_service.cumulative_blame("committer", "cumulative_project_blame.json")

    with open(_artifact("cumulative_project_blame.json")) as handle:
        assert json.load(handle) == EXPECTED_SERIES


def test_failed_serialization_leaves_previous_artifact_byte_for_byte(data_dir):
    """The assertion that actually catches the truncating write.

    ``json.dump`` emits the leading chunks before it reaches the unserializable
    value, so writing has begun by the time it raises.  Dumping into the live
    path would leave those partial bytes (or nothing) behind.
    """
    artifact = _artifact("cumulative_author_blame.json")
    previous = json.dumps(EXPECTED_SERIES, indent=4)
    with open(artifact, "w") as handle:
        handle.write(previous)

    # A set is not JSON-serializable; the preceding key is written first.
    doomed = [{"key": "alice", "values": [[1000, 5]]}, {"key": "bob", "values": {1, 2}}]
    with pytest.raises(TypeError):
        cumulative_blame_service._write_artifact(artifact, doomed)

    with open(artifact) as handle:
        assert handle.read() == previous


def test_failed_serialization_leaves_no_temporary_file(data_dir):
    artifact = _artifact("cumulative_author_blame.json")
    with open(artifact, "w") as handle:
        handle.write("[]")

    with pytest.raises(TypeError):
        cumulative_blame_service._write_artifact(artifact, {1, 2})

    assert os.listdir(os.path.dirname(artifact)) == [os.path.basename(artifact)]
