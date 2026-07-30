"""Tests for ``gitnoc.services.settings``.

These exercise the file-backed JSON profile logic in isolation.  The
``settings_env`` fixture (see ``conftest.py``) redirects the module at a
temporary ``settings.json`` so the repo's real config is never read or written.
"""

import os

import pytest


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


@pytest.mark.parametrize("getter_name", [
    "get_settings",
    "get_profiles",
    "get_file_prefix",
])
def test_malformed_file_raises_parse_error(settings_env, getter_name):
    settings_env.path.write_text("")
    with pytest.raises(ValueError):
        getattr(settings_env.module, getter_name)()


@pytest.mark.parametrize("getter_name", [
    "get_settings",
    "get_profiles",
    "get_file_prefix",
])
def test_file_read_errors_propagate(settings_env, monkeypatch, getter_name):
    def unreadable_file(*args, **kwargs):
        raise PermissionError("settings file is unreadable")

    monkeypatch.setattr("builtins.open", unreadable_file)
    with pytest.raises(PermissionError, match="unreadable"):
        getattr(settings_env.module, getter_name)()


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
        assert c["extensions"] == []
        assert c["ignore_dir"] == []
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


def test_ignore_file_works_for_newly_created_profile(settings_env):
    settings_env.write([])

    settings_env.module.create_profile("new")
    settings_env.module.change_profile("new")
    assert settings_env.module.ignore_file("src-vendor-lib") is True

    assert settings_env.read()[0]["ignore_dir"] == ["src/vendor/lib"]


@pytest.mark.parametrize("legacy_ignore_dir", [None, pytest.param("missing", id="missing")])
def test_ignore_file_normalizes_legacy_ignore_dir(settings_env, legacy_ignore_dir):
    profile = {"profile_name": "legacy", "current_profile": True}
    if legacy_ignore_dir != "missing":
        profile["ignore_dir"] = legacy_ignore_dir
    settings_env.write([profile])

    assert settings_env.module.ignore_file("src-vendor-lib") is True

    assert settings_env.read()[0]["ignore_dir"] == ["src/vendor/lib"]


def test_ignore_file_appends_to_existing_list(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": False, "ignore_dir": []},
        {"profile_name": "b", "current_profile": True, "ignore_dir": ["build"]},
    ])

    assert settings_env.module.ignore_file("src-vendor-lib") is True

    by_name = {c["profile_name"]: c for c in settings_env.read()}
    # Dashes in the encoded path are turned back into path separators.
    assert by_name["b"]["ignore_dir"] == ["build", "src/vendor/lib"]
    assert by_name["a"]["ignore_dir"] == []


# --- fresh checkout (no settings.json) --------------------------------------

def test_create_profile_on_fresh_checkout_creates_file(settings_env):
    # A fresh checkout ships no settings.json; creating a profile must make one.
    assert not settings_env.path.exists()

    assert settings_env.module.create_profile("first") is True

    configs = settings_env.read()
    assert len(configs) == 1
    assert configs[0]["profile_name"] == "first"
    assert configs[0]["current_profile"] is False
    assert configs[0]["project_dir"] is None
    assert configs[0]["extensions"] == []
    assert configs[0]["ignore_dir"] == []
    assert configs[0]["branch"] == "master"


def test_fresh_checkout_profile_round_trip(settings_env):
    # The whole first-run journey: create -> select -> configure.
    settings_env.module.create_profile("first")
    settings_env.module.change_profile("first")
    settings_env.module.update_profile(
        project_dir="/tmp/code", extensions=["py"], ignore_dir=["vendor"], branch="main"
    )

    configs = settings_env.read()
    assert len(configs) == 1
    assert configs[0]["current_profile"] is True
    assert configs[0]["project_dir"] == "/tmp/code"
    assert configs[0]["extensions"] == ["py"]
    assert configs[0]["ignore_dir"] == ["vendor"]
    assert configs[0]["branch"] == "main"


def test_change_profile_on_fresh_checkout_does_not_raise(settings_env):
    assert settings_env.module.change_profile("nope") is True
    assert settings_env.read() == []


def test_update_profile_on_fresh_checkout_does_not_raise(settings_env):
    assert settings_env.module.update_profile(
        project_dir="/tmp/code", extensions=[], ignore_dir=[]
    ) is True
    assert settings_env.read() == []


def test_ignore_file_on_fresh_checkout_is_a_no_op(settings_env):
    assert settings_env.module.ignore_file("src-vendor-lib") is True
    # No profile to ignore for, so no bogus settings file is left behind.
    assert not settings_env.path.exists()


def test_ignore_file_without_current_profile_leaves_file_untouched(settings_env):
    settings_env.write([{"profile_name": "a", "current_profile": False, "ignore_dir": []}])
    before = settings_env.path.read_bytes()

    assert settings_env.module.ignore_file("src-vendor-lib") is True

    assert settings_env.path.read_bytes() == before


# --- writers preserve existing data -----------------------------------------

def test_create_profile_preserves_existing_profiles(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": True, "project_dir": "/tmp/a",
         "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main"},
    ])

    settings_env.module.create_profile("b")

    configs = settings_env.read()
    assert [c["profile_name"] for c in configs] == ["a", "b"]
    assert configs[0]["current_profile"] is True
    assert configs[0]["project_dir"] == "/tmp/a"
    assert configs[0]["extensions"] == ["py"]
    assert configs[0]["ignore_dir"] == ["vendor"]
    assert configs[0]["branch"] == "main"


def test_change_profile_preserves_existing_profile_values(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": True, "project_dir": "/tmp/a",
         "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main"},
        {"profile_name": "b", "current_profile": False, "project_dir": "/tmp/b",
         "extensions": ["js"], "ignore_dir": ["node_modules"], "branch": "master"},
    ])

    settings_env.module.change_profile("b")

    by_name = {c["profile_name"]: c for c in settings_env.read()}
    assert by_name["a"]["project_dir"] == "/tmp/a"
    assert by_name["a"]["extensions"] == ["py"]
    assert by_name["a"]["ignore_dir"] == ["vendor"]
    assert by_name["a"]["branch"] == "main"
    assert by_name["b"]["project_dir"] == "/tmp/b"
    assert by_name["b"]["extensions"] == ["js"]
    assert by_name["b"]["branch"] == "master"


def test_update_profile_preserves_other_profile_values(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": False, "project_dir": "/tmp/a",
         "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main"},
        {"profile_name": "b", "current_profile": True, "project_dir": None,
         "extensions": None, "ignore_dir": None, "branch": "master"},
    ])

    settings_env.module.update_profile(
        project_dir="/tmp/code", extensions=["js"], ignore_dir=["build"], branch="dev"
    )

    by_name = {c["profile_name"]: c for c in settings_env.read()}
    assert by_name["a"] == {
        "profile_name": "a", "current_profile": False, "project_dir": "/tmp/a",
        "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main",
    }
    assert by_name["b"]["project_dir"] == "/tmp/code"
    assert by_name["b"]["branch"] == "dev"


def test_ignore_file_preserves_other_profile_values(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": False, "project_dir": "/tmp/a",
         "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main"},
        {"profile_name": "b", "current_profile": True, "project_dir": "/tmp/b",
         "extensions": ["js"], "ignore_dir": ["build"], "branch": "dev"},
    ])

    settings_env.module.ignore_file("src-vendor-lib")

    by_name = {c["profile_name"]: c for c in settings_env.read()}
    assert by_name["a"]["ignore_dir"] == ["vendor"]
    assert by_name["a"]["project_dir"] == "/tmp/a"
    assert by_name["b"]["ignore_dir"] == ["build", "src/vendor/lib"]
    assert by_name["b"]["project_dir"] == "/tmp/b"
    assert by_name["b"]["extensions"] == ["js"]


# --- atomic writes ----------------------------------------------------------

def test_failed_write_leaves_previous_file_intact(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": True, "project_dir": "/tmp/a",
         "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main"},
    ])
    before = settings_env.path.read_bytes()

    # A set is not JSON-serializable, so json.dump raises partway through.
    with pytest.raises(TypeError):
        settings_env.module.update_profile(
            project_dir="/tmp/code", extensions={"py"}, ignore_dir=[]
        )

    assert settings_env.path.read_bytes() == before


def test_failed_write_leaves_no_temp_file_behind(settings_env):
    settings_env.write([{"profile_name": "a", "current_profile": True}])

    with pytest.raises(TypeError):
        settings_env.module.update_profile(
            project_dir="/tmp/code", extensions={"py"}, ignore_dir=[]
        )

    assert list(settings_env.path.parent.glob("settings.json.*")) == []


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
