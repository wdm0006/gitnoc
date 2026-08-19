"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""

from flask import Blueprint, redirect, url_for
import json

from gitnoc.services.artifact_paths import cumulative_blame_artifact_path
from gitnoc.services.cumulative_blame import cumulative_blame
from gitnoc.services.settings import get_settings
from gitnoc.utils import render_wrapper

__author__ = 'willmcginnis'

blueprint = Blueprint('blame', __name__, static_folder="../static")


@blueprint.route('/blame', methods=["GET"])
def blame():
    return render_wrapper('public/blame.html')


@blueprint.route('/cumulative_author_blame_data', methods=['GET'])
def cumulative_author_blame_data():
    path = cumulative_blame_artifact_path(get_settings().get('profile_name', 'default'), 'cumulative_author_blame.json')
    try:
        return json.dumps(json.load(open(path, 'r')))
    except FileNotFoundError:
        return '{}'


@blueprint.route('/cumulative_author_blame', methods=['GET'])
def cumulative_author_blame():
    from gitnoc.app import q
    if q is not None:
        q.enqueue(cumulative_blame, 'committer', 'cumulative_author_blame.json', job_timeout=60000)
    else:
        cumulative_blame('committer', 'cumulative_author_blame.json')

    return redirect(url_for('blame.blame'))


@blueprint.route('/cumulative_project_blame_data', methods=['GET'])
def cumulative_project_blame_data():
    path = cumulative_blame_artifact_path(get_settings().get('profile_name', 'default'), 'cumulative_project_blame.json')
    try:
        return json.dumps(json.load(open(path, 'r')))
    except FileNotFoundError:
        return '{}'


@blueprint.route('/cumulative_project_blame', methods=['GET'])
def cumulative_project_blame():
    from gitnoc.app import q
    if q is not None:
        q.enqueue(cumulative_blame, 'project', 'cumulative_project_blame.json', job_timeout=60000)
    else:
        cumulative_blame('project', 'cumulative_project_blame.json')

    return redirect(url_for('blame.blame'))
