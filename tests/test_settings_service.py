"""Tests for ``gitnoc.services.settings``.

These exercise the file-backed JSON profile logic in isolation.  The
``settings_env`` fixture (see ``conftest.py``) redirects the module at a
temporary ``settings.json`` so the repo's real config is never read or written.
"""

import os


def assert_safe_defaults(settings):
    assert settings["profile_name"] == "default"
    assert settings["project_dir"] == os.getcwd()
    assert settings["extensions"] == []
    assert settings["ignore_dir"] == []
    assert settings["branch"] == "master"


def test_get_settings_missing_file_returns_default_profile(settings_env):
    # No settings.json on disk at all -> synthetic default, not an exception.
    assert not settings_env.path.exists()
    assert_safe_defaults(settings_env.module.get_settings())


def test_get_settings_empty_file_returns_default_profile(settings_env):
    # An empty/malformed file is swallowed and yields the synthetic default.
    settings_env.path.write_text("")
    assert_safe_defaults(settings_env.module.get_settings())


def test_get_settings_returns_current_profile(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": False},
        {"profile_name": "b", "current_profile": True},
    ])
    assert settings_env.module.get_settings()["profile_name"] == "b"


def test_get_settings_no_current_profile_returns_default(settings_env):
    settings_env.write([{"profile_name": "a", "current_profile": False}])
    assert_safe_defaults(settings_env.module.get_settings())


def test_create_profile_appends(settings_env):
    settings_env.write([])

    assert settings_env.module.create_profile("first") is True
    assert settings_env.module.create_profile("second") is True

    configs = settings_env.read()
    assert [c["profile_name"] for c in configs] == ["first", "second"]
    # New profiles are seeded with the documented defaults.
    for c in configs:
        assert c["current_profile"] is False
        assert c["extensions"] is None
        assert c["ignore_dir"] is None
        assert c["project_dir"] is None
        # A backward-compatible default branch is persisted on creation.
        assert c["branch"] == "master"


def test_change_profile_sets_exactly_one_current(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": True},
        {"profile_name": "b", "current_profile": False},
        {"profile_name": "c", "current_profile": False},
    ])

    assert settings_env.module.change_profile("c") is True

    configs = settings_env.read()
    current = [c["profile_name"] for c in configs if c["current_profile"]]
    assert current == ["c"]
    # Every other profile is explicitly cleared.
    assert all(c["current_profile"] is False for c in configs if c["profile_name"] != "c")


def test_update_profile_writes_only_to_current(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": False,
         "project_dir": None, "extensions": None, "ignore_dir": None},
        {"profile_name": "b", "current_profile": True,
         "project_dir": None, "extensions": None, "ignore_dir": None},
    ])

    assert settings_env.module.update_profile(
        project_dir="/tmp/code", extensions=["py"], ignore_dir=["vendor"]
    ) is True

    by_name = {c["profile_name"]: c for c in settings_env.read()}
    assert by_name["b"]["project_dir"] == "/tmp/code"
    assert by_name["b"]["extensions"] == ["py"]
    assert by_name["b"]["ignore_dir"] == ["vendor"]
    # The non-current profile is left untouched.
    assert by_name["a"]["project_dir"] is None
    assert by_name["a"]["extensions"] is None
    assert by_name["a"]["ignore_dir"] is None


def test_get_profiles_returns_name_choice_tuples(settings_env):
    settings_env.write([
        {"profile_name": "alpha", "current_profile": True},
        {"profile_name": "beta", "current_profile": False},
    ])
    assert settings_env.module.get_profiles() == [("alpha", "alpha"), ("beta", "beta")]


def test_get_profiles_missing_file_returns_empty_list(settings_env):
    assert settings_env.module.get_profiles() == []


def test_get_file_prefix_slugifies_spaces(settings_env):
    settings_env.write([{"profile_name": "My Project Name", "current_profile": True}])
    assert settings_env.module.get_file_prefix() == "My_Project_Name_"


def test_get_file_prefix_no_current_profile_returns_empty(settings_env):
    settings_env.write([{"profile_name": "My Project", "current_profile": False}])
    assert settings_env.module.get_file_prefix() == ""


def test_get_file_prefix_missing_file_returns_empty(settings_env):
    assert settings_env.module.get_file_prefix() == ""


def test_ignore_file_appends_to_current_profile(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": False, "ignore_dir": []},
        {"profile_name": "b", "current_profile": True, "ignore_dir": []},
    ])

    assert settings_env.module.ignore_file("src-vendor-lib") is True

    by_name = {c["profile_name"]: c for c in settings_env.read()}
    # Dashes in the encoded path are turned back into path separators.
    assert by_name["b"]["ignore_dir"] == ["src/vendor/lib"]
    assert by_name["a"]["ignore_dir"] == []


# --- branch selection -------------------------------------------------------

def test_get_settings_missing_branch_normalizes_to_master(settings_env):
    # Profiles created before the branch field existed have no branch key.
    settings_env.write([{"profile_name": "legacy", "current_profile": True}])
    assert settings_env.module.get_settings()["branch"] == "master"


def test_get_settings_blank_branch_normalizes_to_master(settings_env):
    settings_env.write([{"profile_name": "a", "current_profile": True, "branch": ""}])
    assert settings_env.module.get_settings()["branch"] == "master"


def test_get_settings_returns_configured_branch(settings_env):
    settings_env.write([{"profile_name": "a", "current_profile": True, "branch": "main"}])
    assert settings_env.module.get_settings()["branch"] == "main"


def test_update_profile_persists_branch(settings_env):
    settings_env.write([
        {"profile_name": "b", "current_profile": True,
         "project_dir": None, "extensions": None, "ignore_dir": None, "branch": "master"},
    ])

    assert settings_env.module.update_profile(
        project_dir="/tmp/code", extensions=["py"], ignore_dir=["vendor"], branch="main"
    ) is True

    assert settings_env.read()[0]["branch"] == "main"


def test_update_profile_blank_branch_defaults_to_master(settings_env):
    settings_env.write([
        {"profile_name": "b", "current_profile": True,
         "project_dir": None, "extensions": None, "ignore_dir": None, "branch": "main"},
    ])

    settings_env.module.update_profile(
        project_dir="/tmp/code", extensions=None, ignore_dir=None, branch=""
    )

    assert settings_env.read()[0]["branch"] == "master"
