"""Logging configuration for the extraction service."""

import logging
import sys
from pathlib import Path

from config import settings


def setup_logging() -> None:
    """
    Configure logging for the application.
    
    Sets up logging based on configuration from settings:
    - Log level from settings.log_level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Console output (stdout) always enabled
    - File output to settings.log_file if specified
    
    The logging format includes timestamp, logger name, level, file location,
    and the log message for comprehensive debugging.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Configure logging format
    log_format = (
        "%(asctime)s - %(name)s - %(levelname)s - "
        "[%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Always include console handler
    handlers = [logging.StreamHandler(sys.stdout)]
    
    # Add file handler if log_file is specified
    if settings.log_file:
        log_path = Path(settings.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(settings.log_file))
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured at {settings.log_level} level")
    if settings.log_file:
        logger.info(f"Logging to file: {settings.log_file}")

