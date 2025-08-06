"""Utility functions and logging setup with UTF-8 support"""
import logging
import sys
import os
from datetime import datetime

def setup_logging():
    """Set up logging with UTF-8 support for Korean characters"""
    
    # Set the environment variable to force UTF-8 encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Configure logging
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Clear any existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create console handler with UTF-8 encoding
    console_handler = logging.StreamHandler()
    
    # Try to set UTF-8 encoding for the stream handler
    try:
        # For Python 3.7+, try to reconfigure encoding
        if hasattr(console_handler.stream, 'reconfigure'):
            console_handler.stream.reconfigure(encoding='utf-8')
    except Exception:
        # If reconfigure fails, we'll handle it with encoding errors
        pass
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    # Also create a file handler for persistent logs
    file_handler = logging.FileHandler('bot.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    
    logger.info("Logging configured with UTF-8 support for Korean characters")

def safe_log_message(message: str) -> str:
    """Create a safe log message that won't cause encoding errors"""
    try:
        # Try to encode the message to ASCII to test for Unicode characters
        message.encode('ascii')
        return message
    except UnicodeEncodeError:
        # If it contains Unicode, create a safe version
        safe_chars = []
        for char in message:
            try:
                char.encode('ascii')
                safe_chars.append(char)
            except UnicodeEncodeError:
                # Replace Unicode characters with a placeholder
                safe_chars.append(f'[U+{ord(char):04X}]')
        return ''.join(safe_chars)
