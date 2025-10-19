"""
Logging configuration module for AI Market Insight Bot.
Provides production-ready logging with file rotation and multiple log levels.
"""

import logging
import logging.handlers
import os
from pathlib import Path
from config import LOG_LEVEL

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file paths
BOT_LOG_FILE = LOGS_DIR / "bot.log"
ERROR_LOG_FILE = LOGS_DIR / "errors.log"
DATABASE_LOG_FILE = LOGS_DIR / "database.log"
API_LOG_FILE = LOGS_DIR / "api.log"


def setup_logger(name, log_file, level=logging.INFO):
    """
    Setup a logger with file rotation and console output.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler with rotation (10MB per file, keep 5 backups)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    return logger


def setup_all_loggers():
    """Setup all application loggers."""
    log_level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    
    # Main bot logger
    bot_logger = setup_logger('bot', BOT_LOG_FILE, log_level)
    
    # Error logger
    error_logger = setup_logger('errors', ERROR_LOG_FILE, logging.ERROR)
    
    # Database logger
    db_logger = setup_logger('database', DATABASE_LOG_FILE, log_level)
    
    # API logger
    api_logger = setup_logger('api', API_LOG_FILE, log_level)
    
    return {
        'bot': bot_logger,
        'errors': error_logger,
        'database': db_logger,
        'api': api_logger
    }


# Initialize all loggers
LOGGERS = setup_all_loggers()


def get_logger(name):
    """Get a logger by name."""
    return logging.getLogger(name)

