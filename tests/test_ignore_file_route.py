"""The Ignore link must carry a real repository path end to end.

The per-file Ignore action used to encode path separators as dashes and decode
them back, which corrupted every legitimately hyphenated name
(``requirements-dev.txt`` was stored as ``requirements/dev.txt``).  The route now
uses Flask's ``path`` converter, so these tests drive the real blueprint's URL
map: the value the template hands ``url_for`` has to come back out of the
matched URL unchanged, and reach the settings service verbatim.

``views.admin`` pulls in the WTForms stack; it is stubbed when that stack is not
installed so this module still runs on a bare ``pip install pytest Flask``.
Everything under test -- the route rule, the view, and the template's link
expression -- is the real thing either way.
"""
import os
import re
import sys
import types

import pytest

flask = pytest.importorskip("flask")


try:
    import flask_wtf  # noqa: F401
    _has_wtforms = True
except ImportError:
    _has_wtforms = False

if not _has_wtforms and "gitnoc.forms.public" not in sys.modules:
    _forms_stub = types.ModuleType("gitnoc.forms.public")

    class _Form:
        def __init__(self, *args, **kwargs):
            pass

    _forms_stub.SettingsForm = _Form
    _forms_stub.ProfileForm = _Form
    _forms_stub.CreateProfileForm = _Form
    sys.modules["gitnoc.forms.public"] = _forms_stub

from gitnoc.views import admin as admin_view  # noqa: E402


TEMPLATE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'gitnoc', 'templates', 'public', 'repo_detail.html',
)

NESTED_PATH = "src/my-app/main.py"


@pytest.fixture
def app():
    application = flask.Flask(__name__)
    application.register_blueprint(admin_view.blueprint)
    return application


def ignore_link_markup():
    """The template's Ignore-link line, so the test renders what ships."""
    with open(TEMPLATE) as f:
        lines = [line for line in f if 'admin.ignore_file' in line]
    assert len(lines) == 1, "expected exactly one Ignore link in %s" % TEMPLATE
    return lines[0]


@pytest.mark.parametrize("file_name", [
    "requirements-dev.txt",
    "docker-compose.yml",
    NESTED_PATH,
    "src/vendor/lib.py",
])
def test_ignore_url_round_trips_through_the_route(app, file_name):
    with app.test_request_context():
        url = flask.url_for('admin.ignore_file', file_name=file_name)

    endpoint, values = app.url_map.bind('localhost').match(url)

    assert endpoint == 'admin.ignore_file'
    assert values == {'file_name': file_name}


def test_rendered_ignore_link_resolves_back_to_the_file(app):
    """Render the template's own link expression, then match the URL it built."""
    row = {'file_name': NESTED_PATH, 'loc': 10, 'owner': 'a', 'extension': 'py'}

    with app.test_request_context():
        markup = flask.render_template_string(ignore_link_markup(), x=row)

    href = re.search(r'href="([^"]+)"', markup).group(1)
    endpoint, values = app.url_map.bind('localhost').match(href)

    assert endpoint == 'admin.ignore_file'
    assert values['file_name'] == NESTED_PATH


def test_view_hands_the_path_to_the_settings_service(app, monkeypatch):
    recorded = []
    monkeypatch.setattr(admin_view.settings_services, 'ignore_file',
                        lambda file_name: recorded.append(file_name) or True)

    with app.test_request_context():
        url = flask.url_for('admin.ignore_file', file_name=NESTED_PATH)
    response = app.test_client().get(url, query_string={'next': '/'})

    assert response.status_code == 302
    assert recorded == [NESTED_PATH]
