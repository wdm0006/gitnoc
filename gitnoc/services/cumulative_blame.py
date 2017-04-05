import os
import json
from gitpandas import ProjectDirectory
from .settings import get_settings, get_file_prefix

__author__ = 'willmcginnis'


def cumulative_blame(by, file_stub):
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)

    repo = ProjectDirectory(working_dir=project_dir)
    print(extensions)
    print(ignore_dir)
    print(by)
    cb = repo.cumulative_blame(branch='master', ignore_globs=['*/%s/*' % (x, ) for x in ignore_dir], include_globs=['*.%s' % (x, ) for x in extensions], by=by, skip=3, limit=300)
    cb = cb[~cb.index.duplicated()]
    t = json.loads(cb.to_json(orient='columns'))

    d3_data = []
    for committer in t.keys():
        blob = dict()
        blob['key'] = committer
        blob['values'] = []
        for data_point in t[committer].keys():
            blob['values'].append([int(float(data_point)), t[committer][data_point]])
            blob['values'] = sorted(blob['values'], key=lambda x: x[0])
        d3_data.append(blob)

    # dump the data to disk
    filename = get_file_prefix() + file_stub
    json.dump(d3_data, open(str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'w'), indent=4)

    return True
