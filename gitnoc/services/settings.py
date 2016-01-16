import json
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