import json
import os

import pytest

from gitnoc.services import artifact_paths
from gitnoc.views import blame as blame_view


def _redirect_data_dir(tmp_path, monkeypatch):
    fake_file = tmp_path / 'gitnoc' / 'services' / 'artifact_paths.py'
    data_dir = tmp_path / 'gitnoc' / 'static' / 'data'
    data_dir.mkdir(parents=True)
    monkeypatch.setattr(artifact_paths, '__file__', str(fake_file))
    return data_dir


@pytest.mark.parametrize('profile_name', [
    'Engineering Team',
    '../../outside',
    r'..\..\outside',
    '/tmp/absolute',
    r'C:\temp\absolute',
])
def test_profile_artifact_paths_stay_inside_static_data(profile_name, tmp_path, monkeypatch):
    data_dir = _redirect_data_dir(tmp_path, monkeypatch)

    path = artifact_paths.cumulative_blame_artifact_path(
        profile_name, 'cumulative_author_blame.json'
    )

    assert os.path.commonpath([str(data_dir.resolve()), path]) == str(data_dir.resolve())
    assert os.path.dirname(path) == str(data_dir.resolve())
    assert os.path.basename(path).endswith('_cumulative_author_blame.json')


def test_ordinary_profile_name_has_readable_deterministic_identifier():
    first = artifact_paths.profile_artifact_id('Engineering Team')
    second = artifact_paths.profile_artifact_id('Engineering Team')

    assert first == second
    assert first == (
        'Engineering_Team_'
        '775dd1a314b96d8612a8407d6fbb863eb17960ad5c5501ae868c0e9b907d187f'
    )


def test_sanitized_name_collisions_have_distinct_identifiers():
    assert artifact_paths.profile_artifact_id('team/a') != artifact_paths.profile_artifact_id('team?a')


def test_data_route_reads_artifact_from_shared_path(settings_env, tmp_path, monkeypatch):
    profile_name = '../../outside'
    settings_env.write([{'profile_name': profile_name, 'current_profile': True}])
    data_dir = _redirect_data_dir(tmp_path, monkeypatch)
    expected = [{'key': 'Ada', 'values': [[123, 45]]}]
    path = artifact_paths.cumulative_blame_artifact_path(
        profile_name, 'cumulative_author_blame.json'
    )
    with open(path, 'w') as artifact:
        json.dump(expected, artifact)

    response = blame_view.cumulative_author_blame_data()

    assert json.loads(response) == expected
    assert os.path.dirname(path) == str(data_dir.resolve())


@pytest.mark.parametrize('file_stub', ['../result.json', '/tmp/result.json', r'..\result.json'])
def test_artifact_stub_cannot_supply_a_path(file_stub, tmp_path, monkeypatch):
    _redirect_data_dir(tmp_path, monkeypatch)

    with pytest.raises(ValueError):
        artifact_paths.cumulative_blame_artifact_path('profile', file_stub)
