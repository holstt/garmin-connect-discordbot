import argparse
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional, TypeVar

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def dump_json_to_file(json_data: dict[Any, Any], file_path: str | Path):
    logger.debug(f"Dumping json to file '{file_path}'")
    with open(file_path, "w") as f:
        json.dump(json_data, f, indent=4)


def to_YYYYMMDD(date: date) -> str:
    return date.strftime("%Y-%m-%d")


# Loads env variables from .env file in root or from custom path if it has been provided as program argument
def load_env():
    args = _get_args()
    env_path_input: str = args["env"]

    env_path = _get_env_path(path_str=env_path_input)

    # Load environment from .env file if provided
    if env_path:
        logger.info(f"Loading environment file from {env_path}")
        load_dotenv(dotenv_path=env_path)
    else:
        logger.info(
            "No environment file provided. Using environment variables from system."
        )


def _get_args():
    # Load args
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-e", "--env", required=False, help="Path of .env file", type=str, default=None
    )
    args = vars(ap.parse_args())
    return args


# Get environment path if exists
def _get_env_path(path_str: Optional[str]) -> Path | None:
    # Check custom path if provided
    if path_str:
        custom_path = Path(path_str).resolve()
        if not custom_path.exists():
            raise IOError(
                f"No .env file found at specified custom path: '{custom_path}'"
            )
        return custom_path
    # No custom path provided
    else:
        # Check root for default .env file
        if (p := Path(".env")) and p.exists():
            return p

        # No custom and no default .env file found
        return None


T = TypeVar("T")


# A generic function that returns target type from a list of items or fails if not found
def get_concrete_type(items: list[Any], type: type[T]) -> T:
    for item in items:
        if isinstance(item, type):
            return item

    raise ValueError(f"Could not find item of type {type} in list")
