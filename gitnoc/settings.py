import os

__author__ = 'willmcginnis'


class Config(object):
    SECRET_KEY = 'foobar'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = SECRET_KEY
    APP_DIR = os.path.abspath(os.path.dirname(__file__))  # This directory
    PROJECT_ROOT = os.path.abspath(os.path.join(APP_DIR, os.pardir))
    BCRYPT_LOG_ROUNDS = 13
    ASSETS_DEBUG = False
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False


class LocalDevConfig(Config):
    ASSETS_DEBUG = True
    DEBUG = True
    REDIS_URL = 'http://localhost:6379/'
    QUEUES = ['default']
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = "localhost"
    CACHE_REDIS_PORT = "6379"


class DockerConfig(Config):
    ASSETS_DEBUG = True
    DEBUG = False
    REDIS_URL = 'redis://redis:6379/0'
    QUEUES = ['default']
    CACHE_TYPE = 'redis'
    CACHE_REDIS_HOST = "redis"
    CACHE_REDIS_PORT = "6379"
