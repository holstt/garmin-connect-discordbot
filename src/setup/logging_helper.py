import logging
import os
import time
from math import log
from os import environ
from typing import Sequence

logger = logging.getLogger(__name__)


# Read log level from env variable
def get_log_level():
    # Default log level
    default_log_level = "INFO"
    log_level_name = os.getenv("LOG_LEVEL", default_log_level).upper()

    try:
        return logging._nameToLevel[log_level_name]  # type: ignore
    except KeyError:
        valid_levels = ", ".join(logging._nameToLevel.keys())  # type: ignore
        raise ValueError(
            f"Invalid log level: {log_level_name}. Valid log levels are: {valid_levels}"
        )


def setup_logging(base_log_level: int = logging.INFO):
    # Set root logger level
    logging.basicConfig(
        level=base_log_level,
        format="[%(asctime)s] [%(levelname)s] %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC

    # Hide debug messages from these libraries
    disable_debug_loggers = ["matplotlib", "PIL"]
    for logger_name in disable_debug_loggers:
        logging.getLogger(logger_name).setLevel(logging.INFO)


def add_password_filter(password_to_redact: str):
    # Add redacting formatter to all handlers of the root logger
    for handler in logging.root.handlers:
        if handler.formatter:
            redacting_formatter = RedactingFormatter(
                handler.formatter, patterns=[password_to_redact]
            )
            # NB: We overwrite the existing formatter, but RedactingFormatter will keep the original formatting
            handler.setFormatter(
                RedactingFormatter(redacting_formatter, patterns=[password_to_redact])
            )


# Formatter redacts any matching patterns from the final log messages, but keeps the original formatting
class RedactingFormatter(logging.Formatter):
    # Get the original formatter and the patterns to redact
    def __init__(self, orig_formatter: logging.Formatter, patterns: Sequence[str]):
        super().__init__()
        self.orig_formatter = orig_formatter
        self._patterns = patterns

    def format(self, record: logging.LogRecord) -> str:
        # To keep the original formatting, we need to call the original formatter first
        # This is the final message that will be logged i.e. string with placeholders have been replaced etc.
        final_msg = self.orig_formatter.format(record)
        # Now we can redact the patterns from the final message
        for pattern in self._patterns:
            final_msg = final_msg.replace(pattern, "***REDACTED***")
        return final_msg
