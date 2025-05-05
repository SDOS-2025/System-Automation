#!/usr/bin/env python
"""Utility for setting up application logging."""

import logging
import sys
from pathlib import Path

# TODO: Make log level and file path configurable via config_loader
LOG_LEVEL = logging.INFO
LOG_FILE_PATH = Path("logs/assistant.log") # Main log file
HISTORY_LOG_FILE_PATH = Path("logs/log.txt") # LLM History log file
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
HISTORY_LOG_FORMAT = '%(asctime)s - %(message)s' # Simpler format for history

_is_configured = False

def setup_logging(log_level: int = LOG_LEVEL,
                   log_file: Path = LOG_FILE_PATH,
                   history_log_file: Path = HISTORY_LOG_FILE_PATH):
    """Configures root logger and specific loggers like llm_history."""
    global _is_configured
    if _is_configured:
        return

    # --- Configure Root Logger (Console and Main File) --- #
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    standard_formatter = logging.Formatter(LOG_FORMAT)

    # Console Handler for Root
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(standard_formatter)
    root_logger.addHandler(console_handler)

    # Main File Handler for Root
    try:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='w') # Overwrite main log each run
        file_handler.setLevel(log_level)
        file_handler.setFormatter(standard_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        logging.error(f"Failed to configure main file logging to {log_file}: {e}", exc_info=True)

    # --- Configure llm_history Logger (Separate File) --- #
    history_logger = logging.getLogger("llm_history")
    history_logger.setLevel(logging.INFO) # Log INFO level for history
    history_logger.propagate = False # Don't send history logs to root logger/console/main file
    history_formatter = logging.Formatter(HISTORY_LOG_FORMAT)

    try:
        history_log_file.parent.mkdir(parents=True, exist_ok=True)
        history_file_handler = logging.FileHandler(history_log_file, mode='w') # Overwrite history log each run
        history_file_handler.setLevel(logging.INFO)
        history_file_handler.setFormatter(history_formatter)
        history_logger.addHandler(history_file_handler)
    except Exception as e:
        # Log error about history file handler to console/main log
        root_logger.error(f"Failed to configure LLM history file logging to {history_log_file}: {e}", exc_info=True)

    _is_configured = True
    root_logger.info("Logging configured.") # Log config message via root logger

def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance for the given name."""
    # Setup is now called by the main entry point if needed
    # if not _is_configured:
    #     setup_logging()
    return logging.getLogger(name)

# Example Usage:
# if __name__ == '__main__':
#     setup_logging()
#     logger = get_logger("my_module")
#     logger.info("This is an info message.")
#     logger.warning("This is a warning.")
#     try:
#         1 / 0
#     except ZeroDivisionError:
#         logger.error("Caught an error!", exc_info=True) 