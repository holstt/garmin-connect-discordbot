import logging
import os
import time
from datetime import datetime, time
from pathlib import Path
from typing import NamedTuple, Optional
from zoneinfo import ZoneInfo

from pytz import BaseTzInfo
from tzlocal import get_localzone

from src import utils
from src.presentation.login_prompt import LoginPrompt

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


class Config(NamedTuple):
    webhook_url: str  # XXX: Should be type DiscordUrl
    notify_time: time
    email: str
    password: str
    time_zone: ZoneInfo
    session_file_path: Optional[Path]
    webhook_error_url: Optional[str]  # XXX: Should be type DiscordUrl


def get_config() -> Config:
    utils.load_env()

    # Get required
    webhook_url = _get_env_variable_or_fail("WEBHOOK_URL")

    notify_time_of_day_str = _get_env_variable_or_fail("NOTIFY_TIME_OF_DAY")
    time_zone = _get_time_zone("TIME_ZONE")
    notify_time = _get_notify_time(notify_time_of_day_str, time_zone)

    # Get optionals
    session_dir: Optional[Path] = _get_session_dir_if_needed(
        session_dir_env_name="DATA_DIRECTORY_PATH"
    )

    email, password = _get_credentials("GARMIN_EMAIL", "GARMIN_PASSWORD")
    webhook_error_url: Optional[str] = os.environ.get("WEBHOOK_ERROR_URL")

    return Config(
        webhook_url,
        notify_time,
        email,
        password,
        time_zone,
        session_dir,
        webhook_error_url,
    )


def _get_time_zone(env_name: str) -> ZoneInfo:
    value = os.environ.get(env_name)
    if not value:
        local_tz: ZoneInfo = get_localzone()  # type: ignore
        logger.info(f"No time zone provided. Defaulting to local time zone: {local_tz}")

        return local_tz

    return ZoneInfo(value)


def _get_env_variable_or_fail(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ValueError(
            f"The environment variable '{name}' is empty or not set. Please provide a value."
        )
    return value


def _get_session_dir_if_needed(session_dir_env_name: str) -> Optional[Path]:
    path_value = os.environ.get(session_dir_env_name)

    if not path_value:
        logger.info("No session directory path provided.")
        return None

    session_dir = Path(path_value).resolve()
    _ensure_dir_created_with_permissions(session_dir)
    return session_dir


def _ensure_dir_created_with_permissions(session_dir: Path):
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


# Get from env or prompt for credentials
def _get_credentials(email_env_name: str, password_env_name: str):
    email: Optional[str] = os.environ.get(email_env_name)
    password: Optional[str] = os.environ.get(password_env_name)

    if not email or not password:
        logger.info("No credentials provided. Prompting for credentials.")
        email, password = LoginPrompt().show()
    return email, password


# Parses the time and converts it to UTC
def _get_notify_time(time_str: str, time_zone: ZoneInfo) -> time:
    time_obj = time.fromisoformat(time_str)

    # Create a date in the specified time zone
    local_dt = datetime.now(tz=time_zone).replace(
        hour=time_obj.hour,
        minute=time_obj.minute,
        second=time_obj.second,
        microsecond=time_obj.microsecond,
    )

    # Convert the date to UTC and extract the time
    utc_dt = local_dt.astimezone(ZoneInfo("UTC"))
    return utc_dt.time()


# XXX: Old session loading in json format. Ensure logic has been moved to api client.

# def _get_session_data_if_needed(
#     session_file_path: Optional[Path],
# ) -> Optional[str]:
#     if session_file_path:
#         logger.info("Session path provided, trying to load session from disk.")
#         session_data = _load_session_if_exists(session_file_path)
#         return session_data
#     else:
#         logger.info("Not loading session, as no session path was provided.")
#         return None


# Loads a previous session file from disk
# def _load_session(session_file_path: Path) -> Optional[dict[str, Any]]:
#     try:
#         with open(session_file_path, "r") as session_file:
#             loaded_session = json.load(session_file)
#             return loaded_session
#     except json.JSONDecodeError as e:
#         # Re-raise, we do not expect the file being invalid json
#         raise ConfigError("Invalid JSON in session file.") from e

# Try to load a previous session from disk
# def _load_session_if_exists(session_file_path: Path) -> Optional[str]:
#     if session_file_path.exists():
#         logger.info(f"Loading session from file: {session_file_path}")
#         return _load_session(session_file_path)
#     else:
#         logger.info(f"No session file found at: {session_file_path}")
#         return None
