"""Logging configuration for the document automation system."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from config import LOG_FILE


def sanitize_for_console(text: str) -> str:
    """Sanitize text for console output to avoid encoding errors.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for console output
    """
    # Replace common problematic Unicode characters
    replacements = {
        '\u25ba': '>',  # Black right-pointing pointer
        '\u25bc': 'v',  # Black down-pointing triangle
        '\u2022': '*',  # Bullet
        '\u2192': '->',  # Rightwards arrow
        '\u2190': '<-',  # Leftwards arrow
    }
    
    result = text
    for old, new in replacements.items():
        result = result.replace(old, new)
    
    # Encode to the console encoding, replacing any remaining problematic chars
    try:
        encoding = sys.stdout.encoding or 'utf-8'
        result = result.encode(encoding, errors='replace').decode(encoding)
    except Exception:
        # Fallback: remove all non-ASCII
        result = result.encode('ascii', errors='replace').decode('ascii')
    
    return result


class ConsoleFormatter(logging.Formatter):
    """Custom formatter that sanitizes Unicode for console output."""
    
    def format(self, record):
        # Sanitize the message for console output
        if isinstance(record.msg, str):
            record.msg = sanitize_for_console(record.msg)
        result = super().format(record)
        return result


def setup_logger(name: str = "alma_project") -> logging.Logger:
    """Setup and configure logger with console and file handlers.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create logs directory if it doesn't exist
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format for log messages
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console formatter with Unicode sanitization
    console_formatter = ConsoleFormatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (INFO level and above) with sanitization
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (DEBUG level and above, rotating) with UTF-8 encoding
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'  # Ensure UTF-8 encoding for file
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create global logger instance
logger = setup_logger()

