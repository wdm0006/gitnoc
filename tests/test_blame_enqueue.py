"""Cumulative-blame refresh routes must hand rq a job timeout, not a job kwarg.

``Queue.enqueue`` pops ``job_timeout`` out of the call and forwards everything
else to the job function.  The routes used to pass ``timeout=60000``, so the
worker unpickled ``cumulative_blame(by, file_stub, timeout=60000)`` and died with
``unexpected keyword argument 'timeout'`` -- the refresh silently never produced
an artifact.  These tests drive the real blueprint against a queue recorder.
"""
import sys

import pytest

flask = pytest.importorskip("flask")

from gitnoc.views import blame as blame_view  # noqa: E402


class QueueRecorder:
    """Stand-in for the global rq queue; records the enqueue call verbatim."""

    def __init__(self):
        self.calls = []

    def enqueue(self, fn, *args, **kwargs):
        self.calls.append((fn, args, kwargs))
        return None


@pytest.fixture
def app():
    application = flask.Flask(__name__, static_folder=None)
    application.register_blueprint(blame_view.blueprint)
    return application


@pytest.fixture
def queue(monkeypatch):
    recorder = QueueRecorder()
    monkeypatch.setattr(sys.modules['gitnoc.app'], 'q', recorder, raising=False)
    return recorder


@pytest.mark.parametrize("url, by, file_stub", [
    ('/cumulative_author_blame', 'committer', 'cumulative_author_blame.json'),
    ('/cumulative_project_blame', 'project', 'cumulative_project_blame.json'),
])
def test_refresh_enqueues_with_job_timeout(app, queue, url, by, file_stub):
    response = app.test_client().get(url)

    assert response.status_code == 302
    assert len(queue.calls) == 1

    fn, args, kwargs = queue.calls[0]
    assert fn is blame_view.cumulative_blame
    assert args == (by, file_stub)
    assert kwargs == {'job_timeout': 60000}


@pytest.mark.parametrize("url", ['/cumulative_author_blame', '/cumulative_project_blame'])
def test_no_job_argument_leaks_into_the_worker_call(app, queue, url):
    """Anything but ``job_timeout`` is forwarded to ``cumulative_blame`` itself."""
    app.test_client().get(url)

    _, _, kwargs = queue.calls[0]
    assert 'timeout' not in kwargs
