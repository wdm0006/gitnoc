"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""
from gitpandas.cache import RedisDFCache
from flask_cache import Cache


__author__ = 'willmcginnis'

cache = Cache()
gp_cache = RedisDFCache(max_keys=100000, db=3, ttl=3600 * 24 * 7)