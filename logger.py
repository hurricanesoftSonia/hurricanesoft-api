#!/usr/bin/env python3
"""Logging module for HurricaneSoft API."""
import logging
import os
import sys
from datetime import datetime


# Global logger instance
_logger = None


def get_logger():
    """Get or create the global logger instance."""
    global _logger
    if _logger is None:
        _logger = _setup_logger()
    return _logger


def _setup_logger():
    """Setup logger with stdout + file handlers."""
    logger = logging.getLogger('hurricanesoft_api')
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Format: [時間] [LEVEL] [路由] 訊息
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional, configurable via env)
    log_file = os.environ.get('HURRICANESOFT_LOG_FILE')
    if log_file:
        try:
            # Create log directory if needed
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    return logger


def log_request(method, path, user, status_code, duration_ms):
    """Log API request.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        user: Username or 'anonymous'
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
    """
    logger = get_logger()
    username = user if user else 'anonymous'
    logger.info(f"[{path}] {method} {status_code} {username} {duration_ms:.0f}ms")


def log_error(path, error, traceback_str=None):
    """Log error with optional traceback.
    
    Args:
        path: Request path where error occurred
        error: Error message or exception
        traceback_str: Optional traceback string
    """
    logger = get_logger()
    logger.error(f"[{path}] {error}")
    if traceback_str:
        logger.error(traceback_str)


def log_info(message, path=None):
    """Log info message.
    
    Args:
        message: Info message
        path: Optional request path
    """
    logger = get_logger()
    if path:
        logger.info(f"[{path}] {message}")
    else:
        logger.info(message)


def log_warning(message, path=None):
    """Log warning message.
    
    Args:
        message: Warning message
        path: Optional request path
    """
    logger = get_logger()
    if path:
        logger.warning(f"[{path}] {message}")
    else:
        logger.warning(message)
