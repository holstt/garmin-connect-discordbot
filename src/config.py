import logging
import os
import time
from datetime import datetime, time
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from tzlocal import get_localzone

import src.presentation.login_prompt as login
from src import utils
from src.presentation.discord_messages import MessageFormat

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    pass


class Credentials(BaseSettings):
    email: str = Field(default_factory=login.prompt_email)
    password: str = Field(default_factory=login.prompt_password)


# Reads from environment variables
class Config(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter="__")

    webhook_url: str  # XXX: Should be type DiscordUrl
    credentials: Credentials = Field(default_factory=Credentials)
    time_zone: ZoneInfo = Field(default_factory=get_localzone)
    notify_time_of_day: time
    session_file_path: Optional[Path] = None
    webhook_error_url: Optional[str] = None  # XXX: Should be type DiscordUrl
    message_format: MessageFormat

    # Create notify time based on time zone
    @validator("notify_time_of_day")
    def create_notify_time(cls, notify_time: time, values: dict[str, Any]) -> time:
        time_zone: ZoneInfo = values["time_zone"]  # type: ignore

        _get_notify_time(notify_time, time_zone)
        return notify_time

    @validator("session_file_path")
    def create_session_file_path(
        cls, session_file_path: Optional[Path], values: dict[str, Any]
    ) -> Path | None:
        if not session_file_path:
            logger.warn("No session directory path provided.")
            return None
        session_dir = Path(session_file_path).resolve()
        _ensure_dir_created_with_permissions(session_dir)
        return session_file_path


# Parses the time and converts it to UTC
def _get_notify_time(time_obj: time, time_zone: ZoneInfo) -> time:
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


def get_config() -> Config:
    utils.load_env()

    config = Config()  # type: ignore
    return config


# TODO: Generalize and move to infra.filesystem_utils
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
