"""Leaderboard tables must be labelled for what they list and explain empty results.

``metrics.html`` extends ``base.html`` and uses ``{% assets %}``, so the tests
render the template's own source with the layout tags stripped and the
endpoints it links to registered as stand-ins.
"""
import os
import re

import pytest

flask = pytest.importorskip("flask")

TEMPLATES = os.path.join(os.path.dirname(__file__), '..', 'gitnoc', 'templates', 'public')


def _source(name):
    with open(os.path.join(TEMPLATES, name)) as f:
        src = f.read()
    src = re.sub(r'{%\s*extends[^%]*%}', '', src)
    src = re.sub(r'{%\s*assets.*?{%\s*endassets\s*%}', '', src, flags=re.S)
    return re.sub(r'{%\s*(end)?block[^%]*%}', '', src)


def _render(name, **ctx):
    app = flask.Flask(__name__)
    app.add_url_rule('/settings', 'admin.settings', lambda: '')
    app.add_url_rule('/repo/<repo_name>/', 'metrics.repo_details', lambda repo_name: '')
    app.add_url_rule('/ignore/<path:file_name>/', 'admin.ignore_file', lambda file_name: '')
    with app.test_request_context():
        return flask.render_template_string(_source(name), **ctx)


def _tables(html):
    return re.findall(r'<table.*?</table>', html, flags=re.S)


def _cells(table, tag):
    return re.findall(r'<%s(?:\s[^>]*)?>(.*?)</%s>' % (tag, tag), table, flags=re.S)


def _board(label, net):
    return [{'rank': 1, 'label': label, 'net': net}]


def test_metrics_headers_and_body_cells():
    html = _render(
        'metrics.html', repo_names=['api'],
        leaderboard={
            'top_committers': _board('alice', 10),
            'top_extensions': _board('py', 7),
            'top_repositories': _board('api', 5),
        })
    boards = _tables(html)[:3]
    assert [_cells(t, 'th')[1] for t in boards] == ['Committer', 'Extension', 'Repository']
    for table, label in zip(boards, ['alice', '*.py', 'api']):
        assert _cells(table, 'th') == ['#', _cells(table, 'th')[1], 'Net Change']
        assert _cells(table, 'td') == ['1', label, _cells(table, 'td')[2]]
    assert [_cells(t, 'td')[2] for t in boards] == ['10', '7', '5']


def test_metrics_empty_leaderboards_explain_themselves():
    html = _render(
        'metrics.html', repo_names=[],
        leaderboard={'top_committers': [], 'top_extensions': [], 'top_repositories': []})
    for table in _tables(html)[:3]:
        text = ' '.join(_cells(table, 'td'))
        assert 'No commits in the past 21 days on the profile' in text
        assert "project directory and branch in" in text
        assert 'href="/settings"' in text


def test_populated_leaderboard_has_no_empty_state():
    html = _render(
        'metrics.html', repo_names=[],
        leaderboard={
            'top_committers': _board('alice', 10),
            'top_extensions': _board('py', 7),
            'top_repositories': _board('api', 5),
        })
    assert 'No commits' not in html


def test_repo_detail_lists_files_not_committers():
    html = _render(
        'repo_detail.html', repo_name='api',
        file_details=[{'file_name': 'a/b.py', 'loc': 3, 'owner': 'alice', 'extension': 'py'}])
    assert 'Top Committers' not in html
    assert '<h3>Files</h3>' in html
    table = _tables(html)[0]
    assert _cells(table, 'td')[:4] == ['a/b.py', '3', 'alice', 'py']
    assert _cells(table, 'th') == ['File', 'LOC', 'Owner', 'Ext.', 'Ignore']


def test_blame_hint_ids_match_script():
    with open(os.path.join(TEMPLATES, 'blame.html')) as f:
        page = f.read()
    with open(os.path.join(TEMPLATES, '..', '..', 'static', 'js', 'cumulative_blame.js')) as f:
        script = f.read()
    for name in ('author', 'project'):
        hint = 'empty_cumulative_%s_blame' % name
        assert 'id="%s"' % hint in page
        assert "'%s'" % hint in script
    assert 'No data yet' in page and 'click Refresh' in page
