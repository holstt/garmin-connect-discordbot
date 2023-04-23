import json
import logging
import time
from pathlib import Path
from typing import Any


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


def dump_json_to_file(json_data: dict[Any, Any], file_path: str | Path):
    with open(file_path, "w") as f:
        json.dump(json_data, f, indent=4)
