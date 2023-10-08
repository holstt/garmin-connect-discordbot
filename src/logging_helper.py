import logging
import time

logger = logging.getLogger(__name__)


def setup_logging(module_logger_name: str, base_log_level: int = logging.INFO):
    logging.basicConfig(
        level=base_log_level,
        format="[%(asctime)s] [%(levelname)s] %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC

    # Always log debug messages from apscheduler to follow the scheduling process #XXX: We should probably just log it ourselves
    # library_logger = logging.getLogger("apscheduler")
    # library_logger.setLevel(logging.DEBUG)
    # Always log debug messages from our own code XXX: For now, we should be consistent with the log level
    logger = logging.getLogger(module_logger_name)
    logger.setLevel(logging.DEBUG)

    # Hide debug messages from these libraries
    always_info = ["matplotlib", "PIL"]
    for logger_name in always_info:
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
    def __init__(self, orig_formatter: logging.Formatter, patterns: list[str]):
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
