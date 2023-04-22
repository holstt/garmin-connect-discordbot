import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any, Optional

from src.infra.garmin_dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin_dtos.garmin_sleep_response import GarminSleepResponse

logger = logging.getLogger(__name__)

from garminconnect import Garmin, GarminConnectAuthenticationError  # type: ignore

# XXX: Consider handling these errors from garminconnect lib: GarminConnectConnectionError,; GarminConnectTooManyRequestsError,


# Extend the Garmin class to add login including session loading/saving
# session_file_path: From where to save and (if available) load session data. If None, no session handling is done (NB: Avoid authenticating with credentials too often to avoid being rate limited)
class GarminBaseClient(Garmin):
    def __init__(self, email: str, password: str, session_file_path: Optional[Path]):
        super(GarminBaseClient, self).__init__()
        self.username = email
        self.password = password
        self._session_file_path = session_file_path

    def login(self):
        logger.info("Login to Garmin Connect...")

        has_valid_session = False
        if self._session_file_path:
            logger.info("Login using provided session file")
            has_valid_session = self._try_session_login(self._session_file_path)
        else:
            logger.info("No session file path set, skipping session login")

        # If no session or session is invalid (returns None), login using credentials instead
        if not has_valid_session:
            self._password_login()

        # Save session if path is set
        if self._session_file_path:
            logger.info(f"Saving session cookies for future use")
            self._save_session(self._session_file_path)

        logger.info("Login successful")
        return True

    def _save_session(self, session_file_path: Path):
        logger.info(f"Saving session to '{session_file_path}'")
        with open(session_file_path, "w", encoding="utf-8") as f:
            json.dump(self.session_data, f, ensure_ascii=False, indent=4)

    def _try_session_login(self, session_file_path: Path) -> bool:
        logger.info(f"Login using session '{session_file_path}'")
        try:
            self.session_data = self._load_saved_session(session_file_path)
            super().login()
            return True
        except FileNotFoundError:
            logger.warning(f"No session file found at '{session_file_path}'")
            return False
        except GarminConnectAuthenticationError:
            logger.warning("Unable to authenticate: Session is no longer valid.")
            return False
        except json.JSONDecodeError as e:
            # Re-raise, we do not expect the file being invalid json
            raise RuntimeError("Invalid json in session file.") from e

    def _load_saved_session(self, session_file_path: Path):
        # Try to load the previous session
        with open(session_file_path, "r") as f:
            saved_session = json.load(f)
            return saved_session

    def _password_login(self):
        super().login()


class GarminApiClient:
    def __init__(self, base_client: GarminBaseClient) -> None:
        self.base_client = base_client  # Base client from library

    def get_daily_sleep(self, start_date: date, end_date: date) -> GarminSleepResponse:
        # Use internal client "modern_rest_client" directly to get better data. Url not in library.
        response_json: dict[str, Any] = self.base_client.modern_rest_client.get(  # type: ignore
            f"proxy/wellness-service/stats/sleep/daily/{start_date.isoformat()}/{end_date.isoformat()}"
        ).json()

        # Convert to dto object
        response_dto = GarminSleepResponse.from_list(response_json)

        return response_dto

    def get_daily_hrv(self, start_date: date, end_date: date) -> GarminHrvResponse:
        assert self.base_client is not None
        # Note: cdate argument is not validated by garminconnect library but just concatenated to base url, so we pass our own custom string for better data
        response_json = self.base_client.get_hrv_data(
            cdate=f"daily/{start_date.isoformat()}/{end_date.isoformat()}"
        )
        response_dto = GarminHrvResponse.from_dict(response_json)
        return response_dto
