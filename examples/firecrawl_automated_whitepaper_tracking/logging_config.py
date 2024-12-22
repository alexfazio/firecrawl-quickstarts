"""Module for configuring logging across the application."""

import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

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
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def setup_crawler_logging(logger_name: str = 'firecrawl_crawler') -> logging.Logger:
    """Configure logging specifically for the crawler module."""
    return setup_base_logging(
        logger_name=logger_name,
        log_file='crawler.log'
    )

def setup_semantic_filter_logging() -> logging.Logger:
    """Configure logging specifically for the semantic filter module."""
    return setup_base_logging(
        logger_name='semantic_filter',
        log_file=f'semantic_filter_{datetime.now().strftime("%Y%m%d")}.log',
        format_string='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s'
    )

def setup_database_logging() -> logging.Logger:
    """Configure logging specifically for the database module."""
    return setup_base_logging(
        logger_name='database',
        log_file='database.log'
    )
