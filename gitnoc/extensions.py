"""
.. module::
    :platform: Unix, Linux, Windows
    :synopsis:

.. moduleauthor:: Will McGinnis <will@pedalwrencher.com.com>

"""
import os

from flask_caching import Cache
from gitpandas.cache import RedisDFCache


__author__ = 'willmcginnis'

cache = Cache()
gp_cache = RedisDFCache(
    host=os.environ.get('GITNOC_REDIS_HOST', 'localhost'),
    port=int(os.environ.get('GITNOC_REDIS_PORT', '6379')),
    max_keys=100000,
    db=3,
    ttl=3600 * 24 * 7,
)
