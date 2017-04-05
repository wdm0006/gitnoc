from gitnoc.services.settings import *
from flask import render_template

__author__ = 'willmcginnis'


def render_wrapper(template, **kwargs):
    current_profile = get_settings()['profile_name']
    return render_template(template, title='GitNOC', profile_name=current_profile, **kwargs)