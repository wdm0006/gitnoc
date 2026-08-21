"""``get_file_change_rates`` must emit real filenames and only ask for coverage
when a repository can supply it.

``tests/test_service_globs.py`` drives the same service with a fake whose
``to_json`` returns ``"[]"``, so the row-mapping code below it never runs.  These
tests hand the service a *populated* frame and assert the exact rows the Risk
table receives, plus the ``coverage`` keyword git-pandas is handed.
"""
import json

import pytest

from gitnoc.services import file_change_rates as file_change_rates_service

PROFILE = {
    "profile_name": "a",
    "current_profile": True,
    "project_dir": "/tmp/code",
    "extensions": ["py"],
    "ignore_dir": [],
    "branch": "main",
}

# The shape git-pandas' ProjectDirectory.file_change_rates actually returns:
# file identity lives in a ``file`` column and the line count in ``lines``.
RECORDS = [
    {
        'file': 'gitnoc/services/metrics.py',
        'unique_committers': 3,
        'abs_rate_of_change': 12.3456,
        'net_rate_of_change': 4.5678,
        'net_change': 32,
        'abs_change': 86,
        'edit_rate': 7.7778,
        'lines': 32,
        'repository': 'gitnoc',
    },
    {
        'file': 'docs/index.md',
        'unique_committers': 1,
        'abs_rate_of_change': 2.0,
        'net_rate_of_change': 2.0,
        'net_change': 4,
        'abs_change': 4,
        'edit_rate': 0.0,
        'lines': 4,
        'repository': 'docs',
    },
]

COVERED_RECORDS = [
    dict(RECORDS[0], lines_covered=24, total_lines=32, coverage=75.0),
    dict(RECORDS[1], lines_covered=0, total_lines=4, coverage=0.0),
]


class FakeFrame:
    """Stands in for the frame ``ProjectDirectory.file_change_rates`` returns.

    That method ends with ``reset_index(drop=True)``, so the frame always
    arrives on a plain ``RangeIndex`` — resetting it again yields an ``index``
    column of row positions, never the filename.
    """

    def __init__(self, records):
        self.records = [dict(record) for record in records]

    def reset_index(self, level=None, inplace=False, **kwargs):
        records = [dict(record, index=idx) for idx, record in enumerate(self.records)]
        if inplace:
            self.records = records
            return None
        return FakeFrame(records)

    def to_json(self, orient='columns', **kwargs):
        assert orient == 'records', 'the service parses the records orientation'
        return json.dumps(self.records)


class FakeRepo:
    def __init__(self, has_coverage):
        self._has_coverage = has_coverage

    def has_coverage(self):
        return self._has_coverage


def make_recorder(records, coverage_flags=(False, )):
    calls = []

    class FakeProjectDirectory:
        def __init__(self, working_dir=None, cache_backend=None):
            self.repos = [FakeRepo(flag) for flag in coverage_flags]

        def file_change_rates(self, **kwargs):
            calls.append(kwargs)
            return FakeFrame(records)

    return FakeProjectDirectory, calls


@pytest.fixture
def profile(settings_env):
    settings_env.write([PROFILE])
    return settings_env


def test_rows_carry_the_file_path_and_line_count(profile, monkeypatch):
    """Every emitted row is [file, repo, committers, growth, edit, lines, coverage]."""
    fake_pd, _ = make_recorder(RECORDS)
    monkeypatch.setattr(file_change_rates_service, "ProjectDirectory", fake_pd)

    output = file_change_rates_service.get_file_change_rates()

    assert output == {'data': [
        ['gitnoc/services/metrics.py', 'gitnoc', 3, 4.57, 7.78, 32, None],
        ['docs/index.md', 'docs', 1, 2.0, 0.0, 4, None],
    ]}


def test_rows_carry_coverage_when_the_repository_supplies_it(profile, monkeypatch):
    fake_pd, _ = make_recorder(COVERED_RECORDS, coverage_flags=(True, ))
    monkeypatch.setattr(file_change_rates_service, "ProjectDirectory", fake_pd)

    output = file_change_rates_service.get_file_change_rates()

    assert output == {'data': [
        ['gitnoc/services/metrics.py', 'gitnoc', 3, 4.57, 7.78, 32, 75.0],
        ['docs/index.md', 'docs', 1, 2.0, 0.0, 4, 0.0],
    ]}


def test_coverage_is_not_requested_when_no_repository_has_it(profile, monkeypatch):
    """git-pandas projects the coverage columns it was asked for, but a repo with
    no .coverage file silently omits them — so asking is a KeyError."""
    fake_pd, calls = make_recorder(RECORDS, coverage_flags=(False, False))
    monkeypatch.setattr(file_change_rates_service, "ProjectDirectory", fake_pd)

    file_change_rates_service.get_file_change_rates()

    assert [call['coverage'] for call in calls] == [False]


def test_coverage_is_requested_when_one_repository_has_it(profile, monkeypatch):
    """A mixed profile is safe: git-pandas concatenates with sort=True, so one
    repository with coverage is enough for the projection to succeed."""
    fake_pd, calls = make_recorder(COVERED_RECORDS, coverage_flags=(False, True))
    monkeypatch.setattr(file_change_rates_service, "ProjectDirectory", fake_pd)

    file_change_rates_service.get_file_change_rates()

    assert [call['coverage'] for call in calls] == [True]
