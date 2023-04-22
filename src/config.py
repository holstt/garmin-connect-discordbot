import argparse
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

SESSION_FILE_NAME = "session.json"


def get_env():
    load_env()

    # Get required
    webhook_url = get_env_variable_or_fail("WEBHOOK_URL")
    notify_at_hour = int(get_env_variable_or_fail("NOTIFY_AT_HOUR"))
    time_zone_str = get_env_variable_or_fail("TIME_ZONE")

    # Get optionals
    if path_value := os.environ.get("SESSION_DIRECTORY_PATH"):
        session_dir = Path(path_value)
        # Ensure dir exists.
        # We use a session dir instead of a file such that we can mount the dir as a volume when running in docker (it is not possible to mount a non-existing file)
        session_dir.mkdir(parents=True, exist_ok=True)
        session_file = Path(os.path.join(session_dir, SESSION_FILE_NAME))
    else:
        session_file = None

    email: Optional[str] = os.environ.get("GARMIN_EMAIL")
    password: Optional[str] = os.environ.get("GARMIN_PASSWORD")

    notify_at_hour = get_notify_time(notify_at_hour, time_zone_str)

    return (
        email,
        password,
        webhook_url,
        session_file,
        notify_at_hour,
    )


def load_env():
    args = get_args()
    env_path_input: str = args["env"]

    env_path = _get_env_path(path_str=env_path_input)

    # Load environment from .env file if provided
    if env_path:
        logger.info(f"Loading environment file from {env_path}")
        load_dotenv(dotenv_path=env_path)


def get_notify_time(notify_at_hour: int, time_zone: str):
    # Create a date in the specified time zone
    local_tz = ZoneInfo(time_zone)
    local_dt = datetime.now(tz=local_tz).replace(hour=notify_at_hour)

    # Convert the date to UTC
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))

    # Extract the UTC hour
    notify_at_hour = utc_dt.hour
    return notify_at_hour


# Get environment path if exists
def _get_env_path(path_str: Optional[str]) -> Path | None:
    # Check custom path if provided
    if path_str:
        custom_path = Path(path_str)
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


def get_args():
    # Load args
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-e", "--env", required=False, help="Path of .env file", type=str, default=None
    )
    args = vars(ap.parse_args())
    return args


def get_env_variable_or_fail(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"The environment variable '{name}' is empty or not set. Please provide a value."
        )
    return value
