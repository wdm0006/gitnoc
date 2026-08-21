"""A single configured project directory must reach git-pandas as a string.

``ProjectDirectory(working_dir=...)`` means two different things depending on
the type it is handed: a string is a directory to walk for repositories, while
every entry of a list must already *be* a repository.  Typing ``/home/me/repos``
into Settings used to be stored as ``['/home/me/repos']`` -- which finds no
repositories at all, silently and with no error -- while ``/home/me/repos/``
worked, because only a trailing slash converted the value back to a string.

These tests pin the parsed values, on the write path (``SettingsForm.validate``),
in the helper itself, and on the read path (``get_settings``).  ``forms.public``
needs the WTForms stack, which is not a test dependency, so it is loaded against
stub modules -- the form logic under test is the real thing.
"""
import importlib.util
import os
import sys
import types

import pytest

from gitnoc.services.settings import parse_project_dir


# --- the pure helper --------------------------------------------------------

@pytest.mark.parametrize('raw, expected', [
    ('/home/me/repos', '/home/me/repos'),
    ('/home/me/repos/', '/home/me/repos/'),
    ('  /home/me/repos  ', '/home/me/repos'),
    ('/a, /b', ['/a', '/b']),
    ('/a,/b,/c', ['/a', '/b', '/c']),
    # A trailing comma must not leave an empty entry behind: git-pandas would
    # treat '' as a repository path.
    ('/a,', '/a'),
    ('/a, ,/b', ['/a', '/b']),
    (',', None),
    ('', None),
    ('   ', None),
    (None, None),
    # Already-stored shapes come back through the same parser.
    (['/a'], '/a'),
    (['/a', '/b'], ['/a', '/b']),
    ([], None),
])
def test_parse_project_dir_values(raw, expected):
    assert parse_project_dir(raw) == expected


# --- the write path: SettingsForm.validate ----------------------------------

class _Field(object):
    """Stand-in for a WTForms field: the form only ever touches ``.data``."""

    def __init__(self, *args, **kwargs):
        self.data = None


class _StubForm(object):
    def __init__(self, *args, **kwargs):
        pass

    def validate(self, extra_validators=None):
        return True


def _load_forms_module():
    """Import ``gitnoc/forms/public.py`` against stub WTForms modules.

    Loaded under a private name so the canonical ``gitnoc.forms.public`` entry
    other tests stub out is left alone, and the stubs are removed again once the
    module body has run.
    """
    stubs = {}
    wtforms = types.ModuleType('wtforms')
    wtforms.StringField = _Field
    wtforms.SelectField = _Field
    validators = types.ModuleType('wtforms.validators')
    validators.DataRequired = lambda *args, **kwargs: None
    flask_wtf = types.ModuleType('flask_wtf')
    flask_wtf.FlaskForm = _StubForm
    stubs['wtforms'] = wtforms
    stubs['wtforms.validators'] = validators
    stubs['flask_wtf'] = flask_wtf

    saved = {name: sys.modules.get(name) for name in stubs}
    sys.modules.update(stubs)
    try:
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'gitnoc', 'forms', 'public.py',
        )
        spec = importlib.util.spec_from_file_location('gitnoc_forms_public_under_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        for name, previous in saved.items():
            if previous is None:
                del sys.modules[name]
            else:
                sys.modules[name] = previous


forms_public = _load_forms_module()


def validated_form(project_directory, extensions=None, ignore_dir=None, branch=None):
    form = forms_public.SettingsForm()
    form.project_directory.data = project_directory
    form.extensions.data = extensions
    form.ignore_dir.data = ignore_dir
    form.branch.data = branch
    assert form.validate() is True
    return form


@pytest.mark.parametrize('typed', ['/home/me/repos', '/home/me/repos/'])
def test_form_stores_a_single_entry_as_a_string(typed):
    # With or without the trailing slash: a list of one finds no repositories.
    assert validated_form(typed).project_directory.data == typed


def test_form_stores_several_entries_as_a_list():
    assert validated_form('/a, /b').project_directory.data == ['/a', '/b']


def test_form_drops_an_empty_trailing_entry():
    assert validated_form('/a,').project_directory.data == '/a'


def test_form_still_parses_the_other_fields():
    form = validated_form('/repos', extensions='py, js', ignore_dir='vendor', branch=' main ')
    assert form.extensions.data == ['py', 'js']
    assert form.ignore_dir.data == ['vendor']
    assert form.branch.data == 'main'


# --- the read path: get_settings --------------------------------------------

def test_get_settings_collapses_a_single_element_list(settings_env):
    # Profiles saved before this fix hold ['/a']; they must start working
    # without the operator re-saving them.
    settings_env.write([
        {"profile_name": "a", "current_profile": True, "project_dir": ["/a"]},
    ])
    assert settings_env.module.get_settings()["project_dir"] == "/a"


def test_get_settings_keeps_several_paths_as_a_list(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": True, "project_dir": ["/a", "/b"]},
    ])
    assert settings_env.module.get_settings()["project_dir"] == ["/a", "/b"]


def test_get_settings_empty_project_dir_falls_back_to_cwd(settings_env):
    settings_env.write([
        {"profile_name": "a", "current_profile": True, "project_dir": [""]},
    ])
    assert settings_env.module.get_settings()["project_dir"] == os.getcwd()
