"""
Logging configuration for Multi-Agent Reasoning system.
"""

import logging
from colorama import Fore, Style

class ColoredFormatter(logging.Formatter):
    """
    Custom Formatter for Logging that applies color based on log level
    and certain keywords.
    """
    LEVEL_COLORS = {
        logging.DEBUG: Fore.LIGHTYELLOW_EX,
        logging.INFO: Fore.WHITE,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    KEYWORD_COLORS = {
        'HTTP Request': Fore.LIGHTYELLOW_EX,
    }

    def format(self, record):
        message = super().format(record)
        for keyword, color in self.KEYWORD_COLORS.items():
            if keyword in message:
                return color + message + Style.RESET_ALL
        color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
        return color + message + Style.RESET_ALL

def setup_logging():
    """Configure logging for the application."""
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter('%(asctime)s %(levelname)s:%(message)s')
    console_handler.setFormatter(console_formatter)

    file_handler = logging.FileHandler("reasoning.log")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    file_handler.setFormatter(file_formatter)

    logging.basicConfig(
        level=logging.INFO,
        handlers=[console_handler, file_handler],
    )
