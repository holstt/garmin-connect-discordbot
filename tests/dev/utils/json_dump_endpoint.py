import logging

from garminconnect import Garmin  # type: ignore

from src.domain.common import DatePeriod
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.time_provider import TimeProvider
from src.setup import config, logging_helper
from src.setup.garmin_endpoints import GarminEndpoint
from tests.dev.utils.test_utils import save_dto_to_file
from tests.dev.utils import test_utils

logger = logging.getLogger(__name__)
time_provider = TimeProvider()

############################################################
# Dumps json response from garmin api to file for use in tests/debugging to avoid having to call the api

# Specify one or more endpoints to get data for
# ENDPOINTS: list[GarminEndpoint] = [GarminEndpoint.DAILY_SLEEP_SCORE] # Explicitly specify endpoints
ENDPOINTS: list[GarminEndpoint] = list(GarminEndpoint)  # Get all endpoints

# Specify period to get data for
period = DatePeriod.from_last_4_weeks(time_provider.now().date())
# period = DatePeriod.from_last_7_days(time_provider.now().date())

############################################################

deps = test_utils.base_setup(with_login=True)
client = deps.garmin_api_client


for endpoint in ENDPOINTS:
    json_response = client.get_data(
        endpoint,
        period,
    )

    save_dto_to_file(json_response, period, endpoint)
    logger.info(f"Saved json for {endpoint}")
