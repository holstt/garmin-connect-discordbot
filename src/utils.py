import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def dump_json_to_file(json_data: dict[Any, Any], file_path: str | Path):
    logger.debug(f"Dumping json to file '{file_path}'")
    with open(file_path, "w") as f:
        json.dump(json_data, f, indent=4)


def to_YYYYMMDD(date: date) -> str:
    return date.strftime("%Y-%m-%d")
