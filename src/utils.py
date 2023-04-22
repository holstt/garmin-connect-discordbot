import logging
import time


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] %(name)-30s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.Formatter.converter = time.gmtime  # Use UTC

    # Log debug messages from apscheduler to follow the scheduling process
    library_logger = logging.getLogger("apscheduler")
    library_logger.setLevel(logging.DEBUG)
    # Log debug messages from own code
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    return logger
