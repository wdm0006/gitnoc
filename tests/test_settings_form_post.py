"""``POST /settings`` has to reach ``update_profile`` on a modern Flask-WTF.

Two regressions hide behind the same symptom -- the settings page silently stops
saving:

* ``SettingsForm(request.form, csrf_enabled=False)`` was accepted verbatim by
  Flask-WTF 0.11.  From 0.14 the kwarg is ignored, CSRF stays on, and validation
  fails with ``{'csrf_token': ['The CSRF token is missing.']}`` because
  ``settings.html`` hand-rolls its form and renders no token.  The supported
  spelling is ``meta={'csrf': False}``.
* WTForms 3 calls ``validate(extra_validators=...)``, so a zero-argument
  ``SettingsForm.validate`` override raises ``TypeError`` from
  ``validate_on_submit``.

These tests post to the real blueprint with the real form class.
"""
import pytest

flask = pytest.importorskip("flask")
pytest.importorskip("flask_wtf")
pytest.importorskip("wtforms")

# Imported before ``views.admin`` so the real form class is the one the view binds.
from gitnoc.forms.public import SettingsForm  # noqa: E402
from gitnoc.views import admin as admin_view  # noqa: E402


PROFILE = {
    'profile_name': 'default',
    'project_dir': '/repos/',
    'extensions': [],
    'ignore_dir': [],
    'branch': 'master',
}

VALID_POST = {
    'project_directory': '/repos/',
    'extensions': 'py,js',
    'ignore_dir': 'vendor',
    'branch': 'main',
}


@pytest.fixture
def app():
    application = flask.Flask(__name__, static_folder=None)
    application.secret_key = 'test'
    application.register_blueprint(admin_view.blueprint)
    return application


@pytest.fixture
def recorded(monkeypatch):
    """Silence the template render and capture the ``update_profile`` call."""
    calls = []
    monkeypatch.setattr(admin_view, 'render_wrapper', lambda template, **kwargs: 'rendered')
    monkeypatch.setattr(admin_view.settings_services, 'get_settings', lambda: dict(PROFILE))
    monkeypatch.setattr(admin_view.settings_services, 'update_profile',
                        lambda *args: calls.append(args) or True)
    return calls


def test_settings_post_validates_and_updates_the_profile(app, recorded):
    """The form the shipped template posts -- no CSRF token -- has to go through."""
    response = app.test_client().post('/settings', data=VALID_POST)

    assert response.status_code == 200
    assert recorded == [('/repos/', ['py', 'js'], ['vendor'], 'main')]


def test_validate_takes_the_wtforms_3_signature(app):
    """WTForms 3 always passes ``extra_validators`` through to ``validate``."""
    with app.test_request_context('/settings', method='POST', data=VALID_POST):
        form = SettingsForm(flask.request.form, meta={'csrf': False})
        assert form.validate(extra_validators=None) is True
        assert form.errors == {}


def test_settings_get_does_not_update_the_profile(app, recorded):
    response = app.test_client().get('/settings')

    assert response.status_code == 200
    assert recorded == []
