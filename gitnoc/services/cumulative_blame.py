import os
import json
import tempfile
from gitnoc.app import gp_cache
from gitpandas import ProjectDirectory
from .settings import get_settings, get_file_prefix
from .globs import ignore_globs, include_globs

__author__ = 'willmcginnis'


def _artifact_path(filename):
    bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return bp + os.sep + 'static' + os.sep + 'data' + os.sep + filename


def _write_artifact(filename, data):
    """Serialize to a sibling temp file, then atomically rename it into place.

    Dumping straight into ``open(path, 'w')`` truncates the live artifact before
    serialization runs, so the blame data routes -- which read the same path and
    only handle a missing file -- can observe a partial document, and a failed
    dump destroys the last usable result.
    """
    path = _artifact_path(filename)
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix=filename + '.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as tmp_file:
            json.dump(data, tmp_file, indent=4)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def cumulative_blame(by, file_stub):
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    branch = settings.get('branch', 'master')

    repo = ProjectDirectory(working_dir=project_dir, cache_backend=gp_cache)
    cb = repo.cumulative_blame(branch=branch, ignore_globs=ignore_globs(ignore_dir), include_globs=include_globs(extensions), by=by, skip=3, limit=300)
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
    _write_artifact(get_file_prefix() + file_stub, d3_data)

    return True
