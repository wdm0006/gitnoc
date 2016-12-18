"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""

import json
import os
from flask import Blueprint, redirect, url_for
from gitnoc.services.cumulative_blame import *
from gitnoc.utils import render_wrapper
from gitnoc.extensions import q

__author__ = 'willmcginnis'

blueprint = Blueprint('blame', __name__, static_folder="../static")


@blueprint.route('/blame', methods=["GET"])
def blame():
    return render_wrapper('public/blame.html')


@blueprint.route('/cumulative_author_blame_data', methods=['GET'])
def cumulative_author_blame_data():
    filename = get_file_prefix() + 'cumulative_author_blame.json'
    try:
        return json.dumps(json.load(open(str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'r')))
    except FileNotFoundError as e:
        return '{}'


@blueprint.route('/cumulative_author_blame', methods=['GET'])
def cumulative_author_blame():
    q.enqueue(cumulative_blame, 'committer', 'cumulative_author_blame.json', timeout=60000)
    return redirect(url_for('blame.blame'))


@blueprint.route('/cumulative_project_blame_data', methods=['GET'])
def cumulative_project_blame_data():
    filename = get_file_prefix() + 'cumulative_project_blame.json'
    try:
        return json.dumps(json.load(open(str(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + os.sep + 'static' + os.sep + 'data' + os.sep + filename, 'r')))
    except FileNotFoundError as e:
        return '{}'


@blueprint.route('/cumulative_project_blame', methods=['GET'])
def cumulative_project_blame():
    q.enqueue(cumulative_blame, 'project', 'cumulative_project_blame.json', timeout=60000)
    return redirect(url_for('blame.blame'))