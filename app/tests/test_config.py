import os

from app.config import config, Config

def test_config_types():
    assert 'development' in config
    assert 'testing' in config
    assert 'production' in config
    assert 'default' in config

def test_testing_config():
    test_config = config['testing']
    assert test_config.TESTING == True
    assert test_config.DEBUG == False

def test_development_config():
    dev_config = config['development']
    assert dev_config.DEBUG == True
    assert dev_config.TESTING == False

def test_production_config():
    prod_config = config['production']
    assert prod_config.DEBUG == False
    assert prod_config.TESTING == False


def test_config_from_env():
    test_url = "postgresql://testuser:testpass@testhost/testdb"
    Config.set_database_url(test_url)
    assert Config.DATABASE_URL == test_url