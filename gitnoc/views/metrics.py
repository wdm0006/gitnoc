"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""

from gitnoc.services.metrics import *
from gitnoc.utils import render_wrapper
from flask import Blueprint

__author__ = 'willmcginnis'

blueprint = Blueprint('metrics', __name__, static_folder="../static")


@blueprint.route('/', methods=["GET"])
def metrics():
    leaderboard = week_leader_board(n=5)
    repo_names = get_repo_names()
    return render_wrapper('public/metrics.html', leaderboard=leaderboard, repo_names=repo_names)


@blueprint.route('/punchcard_data', methods=['GET'])
def punchchard_data():
    output = get_punchcard()
    return str(output)


@blueprint.route('/repo_details/<repo_name>/', methods=["GET"])
def repo_details(repo_name):
    file_details = get_repo_details(repo_name)
    return render_wrapper('public/repo_detail.html', repo_name=repo_name, file_details=file_details)