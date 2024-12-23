"""Module for configuring logging across the application."""

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from functools import wraps  # Needed for the decorator
from pathlib import Path

def setup_base_logging(
    logger_name: str,
    log_file: str = None,
    log_level: int = logging.INFO,
    format_string: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
) -> logging.Logger:
    """Configure base logging with both file and console handlers.
    
    Args:
        logger_name (str): Name of the logger to configure
        log_file (str, optional): Path to log file. If None, only console logging is used
        log_level (int, optional): Logging level. Defaults to INFO
        format_string (str, optional): Format string for log messages
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory relative to the examples directory
    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        log_path = logs_dir / log_file
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_crawler_logging() -> logging.Logger:
    """
    Configure logging for the crawler with file output in the specified logs directory.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return setup_base_logging(
        logger_name="hf_paper_tracker",
        log_file=f"paper_tracker_{timestamp}.log"
    )

def setup_semantic_filter_logging() -> logging.Logger:
    """Configure logging specifically for the semantic filter module."""
    timestamp = datetime.now().strftime("%Y%m%d")
    return setup_base_logging(
        logger_name='semantic_filter',
        log_file=f'semantic_filter_{timestamp}.log',
        format_string='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    )

def setup_database_logging() -> logging.Logger:
    """Configure logging specifically for the database module."""
    return setup_base_logging(
        logger_name='database',
        log_file='database.log'
    )

def log_function_call(func):
    """Decorator to log entry and exit of functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('semantic_filter')  # or whichever logger name you prefer
        logger.info("Entering %s", func.__name__)
        try:
            result = func(*args, **kwargs)
            logger.info("Exiting %s successfully", func.__name__)
            return result
        except Exception as e:
            logger.error("Error in %s: %s", func.__name__, str(e))
            raise
    return wrapper
