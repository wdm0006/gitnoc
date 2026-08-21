from .settings import get_settings
from .globs import ignore_globs, include_globs
from gitpandas import ProjectDirectory
from gitnoc.app import gp_cache
import json
import os

__author__ = 'willmcginnis'


def get_file_change_rates():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir, cache_backend=gp_cache)

    # git-pandas adds the coverage columns to the projection it applies to the
    # concatenated frame, but a repository with no .coverage file omits them
    # without raising, so asking unconditionally is a KeyError.
    coverage = any(r.has_coverage() for r in repo.repos)

    cb = repo.file_change_rates(ignore_globs=ignore_globs(ignore_dir), include_globs=include_globs(extensions), coverage=coverage, days=7)
    cb.reset_index(inplace=True)
    data = json.loads(cb.to_json(orient='records'))

    output = {'data': []}
    for blob in data:
        row = [blob.get(x, None) for x in ['file', 'repository', 'unique_committers', 'net_rate_of_change', 'edit_rate', 'lines', 'coverage']]
        row = [round(x, 2) if isinstance(x, float) else x for x in row]
        output['data'].append(row)

    return output
