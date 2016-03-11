"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""

import json
from gitnoc.services.file_change_rates import *
from flask import Blueprint
from gitnoc.utils import render_wrapper
from gitnoc.extensions import cache

__author__ = 'willmcginnis'

blueprint = Blueprint('risk', __name__, static_folder="../static")


@blueprint.route('/risk', methods=['GET', 'POST'])
def risk():
    return render_wrapper('public/filechangerates.html')


@blueprint.route('/file_change_rates', methods=['GET'])
def file_change_rates():
    output = get_file_change_rates()
    return json.dumps(output)