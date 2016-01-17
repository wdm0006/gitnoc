from gitnoc.services.settings import get_settings
from gitpandas import ProjectDirectory
import json
import os

__author__ = 'willmcginnis'


def get_file_change_rates():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir)
    cb = repo.file_change_rates(extensions=extensions, ignore_dir=ignore_dir, coverage=True, days=7)
    cb.reset_index(level=0, inplace=True)
    data = json.loads(cb.to_json(orient='records'))

    output = {'data': []}
    for blob in data:
        row = [blob.get(x, None) for x in ['index', 'repository', 'unique_committers', 'net_rate_of_change', 'edit_rate', 'total_lines', 'coverage']]
        row = [round(x, 2) if isinstance(x, float) else x for x in row]
        output['data'].append(row)

    return output