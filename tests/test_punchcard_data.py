"""``/punchcard_data`` must return real JSON built from real Python ints.

The route used to answer with ``str(<list of triples>)`` -- a Python ``repr``,
served as ``text/html``.  That only ever parsed as JSON by coincidence, and the
coincidence ended with numpy 2 (NEP 51), where ``repr(np.int64(5))`` became
``np.int64(5)``: ``punchcard.js`` fetches the route with ``$.getJSON`` and the
chart silently rendered empty axes.

These tests drive the real service and the real view.  The fake git-pandas frame
returns ``NumpyStyleScalar`` cells, which reproduce that repr, so the service's
``int(...)`` coercion and the view's ``jsonify(...)`` are both load-bearing here.
"""
import json

import pytest
from flask import Flask

from gitnoc.services import metrics as metrics_service
from gitnoc.views import metrics as metrics_view


PROFILE = {
    "profile_name": "a", "current_profile": True, "project_dir": "/tmp/code",
    "extensions": ["py"], "ignore_dir": ["vendor"], "branch": "main",
}

TRIPLES = [(1, 22, 4), (3, 9, -2)]


class NumpyStyleScalar:
    """A numpy 2 scalar stand-in: ``repr`` is not ``str`` and it is not an int.

    ``repr(np.int64(4))`` is ``'np.int64(4)'`` under NEP 51, which is what made
    the old ``str(output)`` response invalid JSON.  Keeping the type distinct
    from ``int`` is what stops the ``type(v) is int`` assertion below from being
    vacuously true.
    """

    def __init__(self, value):
        self.value = value

    def __int__(self):
        return self.value

    def __repr__(self):
        return 'np.int64(%d)' % (self.value, )

    def __str__(self):
        return str(self.value)


class _PunchcardFrame:
    """Cells addressed as ``pc.loc[idx, column]``, as pandas allows."""

    columns = ('day_of_week', 'hour_of_day', 'net')

    def __init__(self, triples):
        self.rows = [dict(zip(self.columns, (NumpyStyleScalar(v) for v in triple)))
                     for triple in triples]

    @property
    def shape(self):
        return (len(self.rows), len(self.columns))

    @property
    def loc(self):
        return self

    def __getitem__(self, key):
        idx, column = key
        return self.rows[idx][column]


class FakeProjectDirectory:
    def __init__(self, working_dir=None, cache_backend=None):
        pass

    def punchcard(self, **kwargs):
        return _PunchcardFrame(TRIPLES)


@pytest.fixture
def punchcard_env(settings_env, monkeypatch):
    """Real service and view, fake git-pandas, throwaway settings file."""
    settings_env.write([dict(PROFILE)])
    monkeypatch.setattr(metrics_service, "ProjectDirectory", FakeProjectDirectory)
    return settings_env


@pytest.fixture
def client(punchcard_env):
    app = Flask(__name__, static_folder=None)
    app.register_blueprint(metrics_view.blueprint)
    return app.test_client()


def test_fake_scalar_reproduces_the_numpy_2_repr():
    """Guard the fixture itself: without this the value test proves nothing."""
    scalar = NumpyStyleScalar(4)

    assert repr(scalar) == 'np.int64(4)'
    assert str(scalar) != repr(scalar)
    assert type(scalar) is not int


def test_get_punchcard_returns_builtin_ints(punchcard_env):
    result = metrics_service.get_punchcard('/tmp/code', ['py'], ['vendor'], 'main')

    assert result == [[1, 22, 4], [3, 9, -2]]
    assert all(type(v) is int for row in result for v in row)


def test_punchcard_data_serves_parseable_json(client):
    response = client.get('/punchcard_data')

    assert response.status_code == 200
    assert json.loads(response.get_data(as_text=True)) == [[1, 22, 4], [3, 9, -2]]


def test_punchcard_data_declares_the_json_content_type(client):
    response = client.get('/punchcard_data')

    assert response.mimetype == 'application/json'
