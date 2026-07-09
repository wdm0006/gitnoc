"""Shared pytest fixtures for the gitnoc test suite.

The settings service (``gitnoc.services.settings``) imports ``gitnoc.app`` and
``gitpandas`` at module load time, which would otherwise drag in Flask, redis
and git-pandas just to exercise some pure file-backed JSON logic.  We stub those
modules in ``sys.modules`` *before* importing the service so the tests stay fast
and dependency-free.
"""
import json
import sys
import types

import pytest

# --- Stub the heavy/optional imports pulled in by the settings module --------
if "gitpandas" not in sys.modules:
    _gitpandas_stub = types.ModuleType("gitpandas")
    _gitpandas_stub.ProjectDirectory = object  # only referenced, never called here
    sys.modules["gitpandas"] = _gitpandas_stub

if "gitnoc.app" not in sys.modules:
    _app_stub = types.ModuleType("gitnoc.app")
    _app_stub.gp_cache = None
    sys.modules["gitnoc.app"] = _app_stub

# Import after stubbing so the real Flask/redis/git-pandas stack is never loaded.
from gitnoc.services import settings as settings_service  # noqa: E402


class SettingsEnv:
    """Helper handed to tests for reading/writing the temp ``settings.json``."""

    def __init__(self, module, path):
        self.module = module
        self.path = path

    def write(self, data):
        self.path.write_text(json.dumps(data))

    def read(self):
        return json.loads(self.path.read_text())


@pytest.fixture
def settings_env(tmp_path, monkeypatch):
    """Point the settings module at a throwaway ``settings.json``.

    The module derives its config path from its own ``__file__``::

        bp = dirname(dirname(abspath(__file__)))
        path = bp + os.sep + 'settings.json'

    so we monkeypatch ``__file__`` to a fake location two directories deep under
    ``tmp_path``.  Every read/write then lands on the temp file and the repo's
    real ``gitnoc/settings.json`` is never touched.
    """
    pkg_dir = tmp_path / "gitnoc"
    fake_file = pkg_dir / "services" / "settings.py"
    fake_file.parent.mkdir(parents=True)
    monkeypatch.setattr(settings_service, "__file__", str(fake_file))
    return SettingsEnv(settings_service, pkg_dir / "settings.json")
