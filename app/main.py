
from flask import Flask
from app.config import config, get_db_connection, logger


# Global connection object
global_conn = None
def create_app(config_name='default'):
    global global_conn

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    logger.info(app.config['DATABASE_URL'])
    # Initialize the database connection if it doesn't exist
    if global_conn is None:
        logger.info('Initializing database...')
        global_conn = get_db_connection(app.config['DATABASE_URL'])
        logger.info('Database Initialized.')

    # Register your blueprints
    from app.account.routes import bp as account_bp
    app.register_blueprint(account_bp, url_prefix='/account')

    from app.telegram.routes import telegram_bp
    app.register_blueprint(telegram_bp, url_prefix='/telegram')

    from app.reports.routes import reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')


    
    return app

