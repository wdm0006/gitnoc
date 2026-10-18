import logging
import os
import secrets

__author__ = 'willmcginnis'


class Config(object):
    def __init__(self):
        self.SECRET_KEY = os.environ.get('GITNOC_SECRET_KEY')

    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class LocalDevConfig(Config):
    def __init__(self):
        super().__init__()
        if not self.SECRET_KEY:
            self.SECRET_KEY = secrets.token_hex(32)
            logging.getLogger(__name__).warning(
                'GITNOC_SECRET_KEY is unset; using a temporary development key '
                '(sessions reset on restart).'
            )

    ASSETS_DEBUG = True
    DEBUG = True
    REDIS_URL = 'redis://localhost:6379/0'
    QUEUES = ['default']
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = 6379


class DockerConfig(Config):
    def __init__(self):
        super().__init__()
        if not self.SECRET_KEY:
            raise ValueError('Set GITNOC_SECRET_KEY to a non-empty secret before startup.')

    ASSETS_DEBUG = True
    DEBUG = False
    REDIS_URL = 'redis://redis:6379/0'
    QUEUES = ['default']
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_HOST = "redis"
    CACHE_REDIS_PORT = 6379
