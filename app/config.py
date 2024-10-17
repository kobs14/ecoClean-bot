
import time
import logging
import os
import psycopg2
from psycopg2.extras import RealDictCursor

class Config:
    DEBUG = False
    TESTING = False
    DATABASE_URL = os.getenv('DATABASE_URL')

    @classmethod
    def set_database_url(cls, url):
        cls.DATABASE_URL = url

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    DATABASE_URL = os.getenv('TEST_DATABASE_URL')

class ProductionConfig(Config):
    pass

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)

logger = logging.getLogger(__name__)

def get_db_connection(database_url=None):
    if database_url is None:
        logger.info("database_url is None")
        logger.info(Config.DATABASE_URL)
        database_url = Config.DATABASE_URL
    retries = 5
    while retries > 0:
        try:
            conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
            logger.info("Database connection successful")
            return conn
        except psycopg2.OperationalError as e:
            retries -= 1
            logger.warning(f"Database connection failed. Retrying in 2 seconds... ({retries} attempts left)")
            time.sleep(2)

    logger.error("Failed to connect to the database after multiple attempts")
    raise Exception("Database connection failed")



