import os
import logging
import sys
import json
from logging.handlers import RotatingFileHandler
from functools import wraps
from time import time


def setup_logger(name):
    """
    Configure logger based on the current environment
    - development: Detailed console output + basic file logs
    - testing: Minimal logging based on LOG_LEVEL
    - production: Structured JSON logs for better parsing
    """
    # Get environment and log level settings
    environment = os.getenv("ENVIRONMENT", "development").lower()
    log_level_name = os.getenv("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name, logging.INFO)

    # Create logger
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        logger.setLevel(log_level)

        # Create logs directory if it doesn't exist
        log_dir = os.getenv("LOG_DIR", "../logs")
        os.makedirs(log_dir, exist_ok=True)

        # Set up environment-specific logging
        if environment == "development":
            _setup_development_logging(logger, log_dir, name)
        elif environment == "testing":
            _setup_testing_logging(logger, log_dir, name)
        elif environment == "production":
            _setup_production_logging(logger, log_dir, name)
        else:
            # Default to development if unknown
            _setup_development_logging(logger, log_dir, name)

    return logger


def _setup_development_logging(logger, log_dir, name):
    """Development environment logging: verbose with colors for debugging"""
    # Console handler with colors
    console_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColoredFormatter(console_format))
    logger.addHandler(console_handler)

    # Simple file handler
    file_handler = RotatingFileHandler(
        f"{log_dir}/{name}.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(console_format))
    logger.addHandler(file_handler)


def _setup_testing_logging(logger, log_dir, name):
    """Testing environment logging: minimal output to not clutter test results"""
    # Only log warnings and errors to console during tests
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    console_handler.setLevel(logging.WARNING)
    logger.addHandler(console_handler)

    # File for test logs
    file_handler = RotatingFileHandler(
        f"{log_dir}/test_{name}.log",
        maxBytes=2 * 1024 * 1024,  # 2MB
        backupCount=1
    )
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)


def _setup_production_logging(logger, log_dir, name):
    """Production environment logging: structured JSON logs for parsing"""
    # JSON file handler for machine-readable logs
    json_handler = RotatingFileHandler(
        f"{log_dir}/{name}.json.log",
        maxBytes=20 * 1024 * 1024,  # 20MB
        backupCount=10
    )
    json_handler.setFormatter(JsonFormatter())
    logger.addHandler(json_handler)

    # Critical errors still go to console for visibility
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(console_handler)


class ColoredFormatter(logging.Formatter):
    """Add colors to console logs in development"""
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[41m',  # Red background
        'RESET': '\033[0m'  # Reset color
    }

    def format(self, record):
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"


class JsonFormatter(logging.Formatter):
    """Format logs as JSON for better parsing in production"""

    def format(self, record):
        log_data = {
            'timestamp': self.formatTime(record, self.datefmt),
            'name': record.name,
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Include exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }

        # Include any extra attributes
        for key, value in record.__dict__.items():
            if key not in ['args', 'asctime', 'created', 'exc_info', 'exc_text',
                           'filename', 'funcName', 'id', 'levelname', 'levelno',
                           'lineno', 'module', 'msecs', 'message', 'msg', 'name',
                           'pathname', 'process', 'processName', 'relativeCreated',
                           'stack_info', 'thread', 'threadName']:
                log_data[key] = value

        return json.dumps(log_data)


def log_function(level=logging.DEBUG):
    """Decorator to log function entry/exit with timing and context"""

    def decorator(func):
        # Get logger based on the module the decorator is used in
        logger_name = func.__module__

        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get logger inside wrapper to respect any config changes
            logger = setup_logger(logger_name)

            # Prepare context information for logging
            context = {
                'func_name': func.__name__,  # Renamed 'function' to 'func_name'
                'module_name': func.__module__  # Renamed 'module' to 'module_name'
            }

            # Extract user ID for Telegram handlers if applicable
            if args and hasattr(args[0], 'effective_user'):
                user = args[0].effective_user
                if user:
                    context['user_id'] = user.id

            start_time = time()
            logger.log(level, f"Starting {func.__name__}", extra=context)

            try:
                result = func(*args, **kwargs)
                execution_time = time() - start_time

                # Add timing information
                context['execution_time'] = f"{execution_time:.4f}s"
                logger.log(level, f"Completed {func.__name__}", extra=context)

                return result
            except Exception as e:
                execution_time = time() - start_time
                context['execution_time'] = f"{execution_time:.4f}s"
                context['error_message'] = str(e)  # Renamed 'error' to 'error_message'

                logger.error(f"Exception in {func.__name__}: {str(e)}",
                             exc_info=True, extra=context)
                raise

        return wrapper

    return decorator



# Module-level convenience function
def get_logger(name):
    """Get a configured logger for the specified name"""
    return setup_logger(name)