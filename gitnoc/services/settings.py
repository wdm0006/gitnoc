from gitpandas import ProjectDirectory
import json
from gitnoc.app import gp_cache
import os

__author__ = 'willmcginnis'


def get_settings():
    try:
        bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
        for config in configs:
            if config.get('current_profile', False):
                return config
        return {}
    except:
        return {}


def get_profiles():
    try:
        bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
        choices = []
        for config in configs:
            choices.append((config.get('profile_name', ''), config.get('profile_name', '')))
        return choices
    except:
        return []


def get_file_prefix():
    try:
        bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
        for config in configs:
            if config.get('current_profile', False):
                return config.get('profile_name', '').replace(' ', '_') + '_'
        return ''
    except:
        return ''


def create_profile(profile_name):
    bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    configs.append({
        "profile_name": profile_name,
        "current_profile": False,
        "extensions": None,
        "ignore_dir": None,
        "project_dir": None
    })
    json.dump(configs, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True


def change_profile(profile_name):
    bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    out = []
    for config in configs:
        if config.get('current_profile', True):
            config['current_profile'] = False
        if config.get('profile_name', '') == profile_name:
            config['current_profile'] = True
        out.append(config)
    json.dump(out, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True


def update_profile(project_dir, extensions, ignore_dir):
    bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    out = []
    for config in configs:
        if config.get('current_profile', False):
            config['project_dir'] = project_dir
            config['extensions'] = extensions
            config['ignore_dir'] = ignore_dir
        out.append(config)
    json.dump(out, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True


def setup_repos_object():
    settings = get_settings()
    project_dir = settings.get('project_dir', os.getcwd())
    extensions = settings.get('extensions', None)
    ignore_dir = settings.get('ignore_dir', None)
    repo = ProjectDirectory(working_dir=project_dir, cache_backend=gp_cache)
    return repo


def ignore_file(file_name):
    bp = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    configs = json.load(open(bp + os.sep + 'settings.json', 'r'))
    out = []
    for config in configs:
        if config.get('current_profile', False):
            config['ignore_dir'].append(file_name.replace('-', '/'))
        out.append(config)
    json.dump(out, open(bp + os.sep + 'settings.json', 'w'), indent=4)
    return True