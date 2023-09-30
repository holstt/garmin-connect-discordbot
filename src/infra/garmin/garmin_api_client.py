import json
import logging
import os
from datetime import date, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import garth
import requests  # type: ignore
from garminconnect import Garmin, GarminConnectAuthenticationError  # type: ignore
from garth.exc import GarthHTTPError

import src.utils as utils
from src.infra.time_provider import TimeProvider  # type: ignore

# XXX: Consider handling these errors from garminconnect lib: GarminConnectConnectionError,; GarminConnectTooManyRequestsError,


logger = logging.getLogger(__name__)


class GarminApiClientError(Exception):
    pass


# 'garminconnect' library only supports fetching data for a single day, so we define date range endpoints and use garminconnect's internal client directly to fetch.
class GarminEndpoint(Enum):
    DAILY_SLEEP = "/wellness-service/stats/sleep/daily/{start_date}/{end_date}"
    DAILY_SLEEP_SCORE = (
        "/wellness-service/stats/daily/sleep/score/{start_date}/{end_date}"
    )
    DAILY_HRV = "daily/{start_date}/{end_date}"


# Wraps the base client from garminconnect ext. library. We need to modify the endpoint urls in order to get a range of data instead of just one day
# Also handles session loading/saving #XXX: Maybe delegate this resp.
class GarminApiClient:
    def __init__(
        self,
        base_client: Garmin,  # Base client from library
        time_provider: TimeProvider,
        session_dir: Optional[  # From where to save and (if available) load session data. If None, no session handling is done (NB: Avoid authenticating with credentials too often to avoid being rate limited)
            Path
        ] = None,  # XXX: Should take a file saver instead of a path
    ) -> None:
        self._base_client = base_client
        self._session_dir = session_dir
        self._time_provider = time_provider
        self._client_age = time_provider.now()
        if self._session_dir:
            logger.info(
                f"Session file path provided. Will save session data to {session_dir}"
            )
        else:
            logger.info(
                "No session file path provided. Session will only be kept in memory."
            )

    # Authenticate with garmin.
    # May be called initially by external callers to confirm that client is able to login.
    # Client will relogin automatically when needed (if session has expired). XXX: Not sure new version of garminconnect library does this.
    def login(self):
        # Log in and save the session to disk XXX: Make a base class that handles this?
        # NB: If session has expired, internal client will automatically try to re-login.

        if self._session_dir:
            try:
                logger.info(f"Logging in using session data from '{self._session_dir}'")
                self._base_client.login(tokenstore=str(self._session_dir))
                logger.info(f"Succesfully logged in using session data")
                return  # Early return if session data was valid

            # XXX: Catch also GarminConnectAuthenticationError,  GarthHTTPError?
            # Fails if session data does not exist
            except FileNotFoundError as e:
                logger.warning("Session data not found.")
            # Fails if session has expired/invalid
            except GarthHTTPError as e:
                if e.error.response.status_code == 401:
                    logger.warning("Session data invalid.")
                else:
                    raise e

        logger.info("Logging in using credentials.")
        # Login without session data (will use username/password)
        self._base_client.login()  # XXX: What exceptions can be thrown here?
        logger.info("Login successful.")
        # Save the new session data
        if self._session_dir:
            logger.info(f"Saving current session to '{self._session_dir}'")
            self._base_client.garth.dump(str(self._session_dir))

    def get_data(
        self, endpoint: GarminEndpoint, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """
        Fetch data from the specified endpoint between start_date and end_date.
        """

        self.reinit_client_if_needed()

        endpoint_template = endpoint.value
        endpoint_str = self._format_endpoint(endpoint_template, start_date, end_date)

        # Special case for hrv # XXX: Or can we use the same url?
        # XXX: Not using same pattern as get_data() atm
        if endpoint == GarminEndpoint.DAILY_HRV:
            # Note: cdate argument is not validated by garminconnect library but just concatenated to base url, so we pass our own custom string for better data
            request_func = lambda: self._base_client.get_hrv_data(cdate=endpoint_str)
        else:
            request_func = lambda: self._get(endpoint_str)

        response_json = self._execute_request(request_func)
        return response_json

    # XXX: When running on remote server, Garmin base client stops working after a while. (seems not to be a session issue)
    # XXX: This is a workaround for now. Should be investigated further.
    # NB: Not used after migrating to garminconnect 0.2.7 to see if it fixes the issue.
    def reinit_client_if_needed(self):
        return
        max_client_age = timedelta(minutes=1)
        # Reinit if more than max_client_age has passed since last init
        if (self._time_provider.now() - self._client_age) > max_client_age:
            logger.info(
                f"Base client instance exceeds max age: {max_client_age}. Reinitializing client and logging in again."
            )
            self._base_client = Garmin(
                email=self._base_client.username,
                password=self._base_client.password,
                session_data=self._base_client.session_data,
            )
            self._client_age = self._time_provider.now()
            self.login()

    # Injects start and end date into given endpoint url template
    def _format_endpoint(
        self, endpoint_template: str, start_date: date, end_date: date
    ) -> str:
        return endpoint_template.format(
            start_date=utils.to_YYYYMMDD(start_date),
            end_date=utils.to_YYYYMMDD(end_date),
        )

    def _get(self, endpoint_url: str) -> dict[str, Any]:
        try:
            # Use base client's internal http client directly to get better data for urls not in library
            response_json: dict[str, Any] = self._base_client.connectapi(endpoint_url)  # type: ignore

        except requests.exceptions.JSONDecodeError as e:
            raise GarminApiClientError(
                f"Failed to decode response from Garmin: {e}. For endpoint: {endpoint_url}"
            ) from e

        return response_json  # type: ignore

    # General executor, that catches any exceptions thrown by the request function and retries request after re-login
    def _execute_request(self, request_func: Callable[[], dict[str, Any]]):
        try:
            # Execute request (using current session)
            # If it fails, the session may be invalid or expired
            logger.debug("Executing request")
            return request_func()
        # XXX: Catch all for now. Should be more specific.
        # XXX: Fails when session has expired?
        except Exception as e:
            # On failure, try to re-login and execute again. If fails again, we just let the exception propagate.
            logger.exception(
                f"Exception '{type(e).__name__}' occured while fetching data from garmin: {e}. Will try recovering by doing a re-login and fetch again."
            )
            self.login()
            return request_func()

    # XXX: Old session saving in json format
    # def _save_current_session_if_needed(self):
    #     if not self._session_file_path:
    #         logger.info("No session file path provided. Not saving session.")
    #         return

    #     logger.info(f"Saving the current session to '{self._session_file_path}'")

    #     permissions = 0o700  # Owner: read-write-execute, Group: none, Others: none
    #     # os.O_CREAT ensures the file exists (creates it if it doesn't)
    #     # os.O_WRONLY opens the file in write-only mode
    #     # os.O_TRUNC truncates the file before writing, removing any previous content
    #     file_descriptor = os.open(
    #         self._session_file_path, os.O_CREAT | os.O_WRONLY | os.O_TRUNC, permissions
    #     )

    #     with os.fdopen(file_descriptor, "w", encoding="utf-8") as f:
    #         json.dump(self._base_client.session_data, f, ensure_ascii=False, indent=4)
    #
