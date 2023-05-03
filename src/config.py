import argparse
import json
import logging
import os
import time
from datetime import datetime, time
from pathlib import Path

# from time import struct_time
from typing import Any, NamedTuple, Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.presentation.login_prompt import LoginPrompt

logger = logging.getLogger(__name__)

SESSION_FILE_NAME = "session.json"

# XXX: Too much is going on in here -> Delegate


class ConfigError(Exception):
    pass


class Config(NamedTuple):
    webhook_url: str
    notify_time: time
    email: str
    password: str
    session_file_path: Optional[Path]
    session_data: Optional[dict[str, Any]]


def get_config() -> Config:
    _load_env()

    # Get required
    webhook_url = _get_env_variable_or_fail(
        "WEBHOOK_URL"
    )  # XXX: Should be type ValidDiscordUrl
    notify_time_of_day_str = _get_env_variable_or_fail("NOTIFY_TIME_OF_DAY")
    time_zone_str = _get_env_variable_or_fail("TIME_ZONE")

    # Get optionals
    session_file_path: Optional[Path] = _get_session_path_if_needed(
        session_dir_env_name="DATA_DIRECTORY_PATH"
    )
    session_data = _get_session_data_if_needed(session_file_path)

    email: Optional[str] = os.environ.get("GARMIN_EMAIL")
    password: Optional[str] = os.environ.get("GARMIN_PASSWORD")
    # Check if we need to prompt for credentials
    email, password = _get_input_credentials_if_needed(
        email, password, session_file_path
    )

    notify_time = _get_notify_time(notify_time_of_day_str, time_zone_str)

    return Config(
        webhook_url,
        notify_time,
        email,
        password,
        session_file_path,
        session_data,
    )


def _get_session_data_if_needed(
    session_file_path: Optional[Path],
) -> Optional[dict[str, Any]]:
    if session_file_path:
        logger.info("Session path provided, trying to load session from disk.")
        session_data = _load_session_if_exists(session_file_path)
        return session_data
    else:
        logger.info("Not loading session, as no session path was provided.")
        return None


# Loads a previous session file from disk
def _load_session(session_file_path: Path) -> Optional[dict[str, Any]]:
    try:
        with open(session_file_path, "r") as session_file:
            loaded_session = json.load(session_file)
            return loaded_session
    except json.JSONDecodeError as e:
        # Re-raise, we do not expect the file being invalid json
        raise ConfigError("Invalid JSON in session file.") from e


# Try to load a previous session from disk
def _load_session_if_exists(session_file_path: Path) -> Optional[dict[str, Any]]:
    if session_file_path.exists():
        logger.info(f"Loading session from file: {session_file_path}")
        return _load_session(session_file_path)
    else:
        logger.info(f"No session file found at: {session_file_path}")
        return None


def _get_session_path_if_needed(session_dir_env_name: str) -> Optional[Path]:
    path_value = os.environ.get(session_dir_env_name)

    if not path_value:
        logger.info("No data directory path provided.")
        return None

    # The data directory for storing app data.
    session_dir = Path(path_value)

    ensure_dir_created_with_permissions(session_dir)

    # We will store the session file in the data directory if provided.
    session_file_path = Path(os.path.join(session_dir, SESSION_FILE_NAME))

    return session_file_path


def ensure_dir_created_with_permissions(session_dir: Path):
    # Create the directory if it does not exist.
    if not session_dir.exists():
        logger.info(
            f"Data directory does not exist. Creating directory on specified path: {session_dir}"
        )

        try:
            # Create the directory with permission only for the current user.
            session_dir.mkdir(mode=0o700)
        except PermissionError as e:
            raise ConfigError(
                f"Error: Cannot create the data directory '{session_dir}'. No write permission."
            ) from e
    # If exists, ensure that it is a directory and that we have correct permissions.
    else:
        if not session_dir.is_dir():
            raise ConfigError(
                f"Error: The data directory path '{session_dir}' is not a directory."
            )
        # Check if we have permissions
        if not os.access(session_dir, os.R_OK | os.W_OK | os.X_OK):
            raise ConfigError(
                f"Error: Missing permissions for data directory '{session_dir}'."
            )

        logger.info(f"Data directory exists and is accessible: {session_dir}")


def _get_input_credentials_if_needed(
    email: Optional[str], password: Optional[str], session_file_path: Optional[Path]
):
    # if (not session_file_path) and (not email or not password):
    # Prompt for credentials if not provided
    if not email or not password:
        logger.info(
            "No existing session and no credentials provided. Prompting for credentials."
        )
        email, password = LoginPrompt().show()
    return email, password


def _load_env():
    args = _get_args()
    env_path_input: str = args["env"]

    env_path = _get_env_path(path_str=env_path_input)

    # Load environment from .env file if provided
    if env_path:
        logger.info(f"Loading environment file from {env_path}")
        load_dotenv(dotenv_path=env_path)


# Parses the time and converts it to UTC
def _get_notify_time(time_str: str, time_zone: str) -> time:
    time_obj = time.fromisoformat(time_str)
    local_tz = ZoneInfo(time_zone)

    # Create a date in the specified time zone
    local_dt = datetime.now(tz=local_tz).replace(
        hour=time_obj.hour,
        minute=time_obj.minute,
        second=time_obj.second,
        microsecond=time_obj.microsecond,
    )

    # Convert the date to UTC and extract the time
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt.time()


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


def _get_args():
    # Load args
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-e", "--env", required=False, help="Path of .env file", type=str, default=None
    )
    args = vars(ap.parse_args())
    return args


def _get_env_variable_or_fail(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"The environment variable '{name}' is empty or not set. Please provide a value."
        )
    return value
