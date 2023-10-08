import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Callable, Optional, Union

import requests  # type: ignore
from garminconnect import Garmin  # type: ignore
from garth.exc import GarthHTTPError

from src.domain.common import DatePeriod
from src.infra.garmin.garmin_endpoints import GarminEndpoint
from src.infra.time_provider import TimeProvider  # type: ignore

# XXX: Consider handling these errors from garminconnect lib: GarminConnectConnectionError,; GarminConnectTooManyRequestsError,

logger = logging.getLogger(__name__)

# type alias for json
JsonResponseType = Union[dict[Any, Any], list[Any]]


class GarminApiClientError(Exception):
    pass


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
        super().__init__()
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

    # TODO: Move responsibility for auth
    # Authenticate with garmin.
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
        self, endpoint: GarminEndpoint, period: DatePeriod
    ) -> Optional[JsonResponseType]:
        """
        Fetch data from the specified endpoint between start_date and end_date.
        return: Json
        """

        self._reinit_client_if_needed()
        endpoint_str = endpoint.format(period.start, period.end)
        request_func = lambda: self._get(endpoint_str)
        response_json = self._execute_request(request_func)
        return response_json

    # XXX: When running on remote server, Garmin base client stops working after a while. (seems not to be a session issue)
    # XXX: This is a workaround for now. Should be investigated further.
    # NB: Not used after migrating to garminconnect 0.2.7 to see if it fixes the issue.
    def _reinit_client_if_needed(self):
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

    # Returns json response as dict, list. None if response is empty
    def _get(self, endpoint_url: str) -> Optional[JsonResponseType]:
        try:
            # Use base client's internal http client directly to get better data for urls not in library
            response_json: Optional[JsonResponseType] = self._base_client.connectapi(
                endpoint_url
            )

        except requests.exceptions.JSONDecodeError as e:
            raise GarminApiClientError(
                f"Failed to decode response from Garmin: {e}. For endpoint: {endpoint_url}"
            ) from e

        return response_json

    # General executor, that catches any exceptions thrown by the request function and retries request after re-login
    def _execute_request(
        self, request_func: Callable[[], Optional[JsonResponseType]]
    ) -> Optional[JsonResponseType]:
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
