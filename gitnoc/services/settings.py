from gitpandas import ProjectDirectory
import json
from gitnoc.app import gp_cache
import os
import tempfile

__author__ = 'willmcginnis'


def default_settings():
    """Safe defaults so the app degrades gracefully when no profile is configured.

    Used when ``settings.json`` is missing or no profile is marked current.
    Returning these keys (rather than ``{}``) keeps ``render_wrapper`` and the
    service modules from crashing on a fresh install.
    """
    return {
        'profile_name': 'default',
        'project_dir': os.getcwd(),
        'extensions': [],
        'ignore_dir': [],
        'branch': 'master',
    }


def normalize_settings(config):
    """Fill missing keys and coerce ``None`` extensions/ignore_dir to ``[]``.

    Legacy profiles may contain ``None`` for these fields, which breaks the
    glob comprehensions in the service modules. Normalizing here means callers
    never receive ``None``.
    """
    settings = default_settings()
    settings.update({k: v for k, v in config.items() if v is not None})
    if not settings.get('project_dir'):
        settings['project_dir'] = os.getcwd()
    for key in ('extensions', 'ignore_dir'):
        if settings.get(key) is None:
            settings[key] = []
    # Profiles created before the branch field existed (or with a blank value)
    # fall back to master so existing configuration keeps working.
    if not settings.get('branch'):
        settings['branch'] = 'master'
    return settings


def _settings_path():
    bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return bp + os.sep + 'settings.json'


def _load_settings():
    try:
        with open(_settings_path(), 'r') as settings_file:
            return json.load(settings_file)
    except FileNotFoundError:
        return None


def _load_settings_for_write():
    """Profile list to mutate, treating a missing file as "no profiles yet".

    Writers run before ``settings.json`` exists on a fresh checkout. Malformed
    JSON still propagates, matching the read paths.
    """
    configs = _load_settings()
    return [] if configs is None else configs


def _write_settings(configs):
    """Serialize to a sibling temp file, then atomically rename it into place.

    Dumping straight into ``open(path, 'w')`` truncates before serialization
    runs, so a failure mid-dump would leave an empty or half-written file --
    which now breaks every page, since malformed JSON propagates.
    """
    path = _settings_path()
    fd, tmp_path = tempfile.mkstemp(dir=os.path.dirname(path), prefix='settings.json.', suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as tmp_file:
            json.dump(configs, tmp_file, indent=4)
        os.replace(tmp_path, path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def get_settings():
    configs = _load_settings()
    if configs is None:
        return default_settings()
    for config in configs:
        if config.get('current_profile', False):
            return normalize_settings(config)
    return default_settings()


def get_profiles():
    configs = _load_settings()
    if configs is None:
        return []
    choices = []
    for config in configs:
        choices.append((config.get('profile_name', ''), config.get('profile_name', '')))
    return choices


def get_file_prefix():
    configs = _load_settings()
    if configs is None:
        return ''
    for config in configs:
        if config.get('current_profile', False):
            return config.get('profile_name', '').replace(' ', '_') + '_'
    return ''


def create_profile(profile_name):
    configs = _load_settings_for_write()
    configs.append({
        "profile_name": profile_name,
        "current_profile": False,
        "extensions": [],
        "ignore_dir": [],
        "project_dir": None,
        "branch": "master"
    })
    _write_settings(configs)
    return True


def change_profile(profile_name):
    configs = _load_settings_for_write()
    out = []
    for config in configs:
        if config.get('current_profile', True):
            config['current_profile'] = False
        if config.get('profile_name', '') == profile_name:
            config['current_profile'] = True
        out.append(config)
    _write_settings(out)
    return True


def update_profile(project_dir, extensions, ignore_dir, branch='master'):
    configs = _load_settings_for_write()
    out = []
    for config in configs:
        if config.get('current_profile', False):
            config['project_dir'] = project_dir
            config['extensions'] = extensions
            config['ignore_dir'] = ignore_dir
            config['branch'] = branch or 'master'
        out.append(config)
    _write_settings(out)
    return True


def setup_repos_object():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir, cache_backend=gp_cache)
    return repo


def ignore_file(file_name):
    configs = _load_settings_for_write()
    out = []
    changed = False
    for config in configs:
        if config.get('current_profile', False):
            config['ignore_dir'] = config.get('ignore_dir') or []
            config['ignore_dir'].append(file_name)
            changed = True
        out.append(config)
    # With no profile to ignore the file for there is nothing to persist, so
    # don't create a settings.json that holds no configuration.
    if changed:
        _write_settings(out)
    return True
