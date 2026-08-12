import hashlib
import os
import re
import unicodedata


def _data_dir():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static', 'data')


def profile_artifact_id(profile_name):
    display_name = str(profile_name)
    normalized = unicodedata.normalize('NFKD', display_name).encode('ascii', 'ignore').decode('ascii')
    safe_name = re.sub(r'[^A-Za-z0-9]+', '_', normalized).strip('_')[:48] or 'profile'
    digest = hashlib.sha256(display_name.encode('utf-8')).hexdigest()
    return '{}_{}'.format(safe_name, digest)


def cumulative_blame_artifact_path(profile_name, file_stub):
    if os.path.basename(file_stub) != file_stub or '\\' in file_stub:
        raise ValueError('Cumulative-blame artifact name must not contain a path')

    data_dir = os.path.realpath(_data_dir())
    path = os.path.realpath(os.path.join(data_dir, '{}_{}'.format(profile_artifact_id(profile_name), file_stub)))
    if os.path.commonpath([data_dir, path]) != data_dir:
        raise ValueError('Cumulative-blame artifact path escapes the data directory')
    return path
