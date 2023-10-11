import argparse
import json
import logging
from datetime import date
from pathlib import Path
from typing import Any, Optional, Sequence, TypeVar

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
def find_first_of_type_or_fail(items: Sequence[Any], type: type[T]) -> T:
    item = find_first_of_type(items, type)
    if item:
        return item
    else:
        raise ValueError(f"Could not find item of type {type} in list")


def find_first_of_type(items: Sequence[Any], type: type[T]) -> T | None:
    for item in items:
        if isinstance(item, type):
            return item

    return None


# Returns a list of moving averages for a given list of values
# A Value will be None if there are not enough values to calculate the moving average
# The first index with a non-None value will be at index window_size - 1
def get_moving_average(
    values: Sequence[float], window_size: int
) -> Sequence[float | None]:
    moving_averages: Sequence[Optional[float]] = []

    for i in range(1, len(values) + 1):
        if i < window_size:
            moving_averages.append(None)
        else:
            moving_averages.append(sum(values[i - window_size : i]) / window_size)
    return moving_averages
