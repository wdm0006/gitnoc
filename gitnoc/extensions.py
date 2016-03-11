"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""

from redis import Redis
from rq import Queue
from flask_cache import Cache


__author__ = 'willmcginnis'

q = Queue(connection=Redis())

cache = Cache(config={'CACHE_TYPE': 'simple'})