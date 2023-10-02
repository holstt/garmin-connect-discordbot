import logging

from garminconnect import Garmin  # type: ignore

from src import config, logging_helper
from src.domain.models import DatePeriod
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.garmin.garmin_endpoints import GarminEndpoint
from src.infra.time_provider import TimeProvider
from tests.dev.test_utils import save_dto_to_file

logger = logging.getLogger(__name__)
time_provider = TimeProvider()

############################################################
# Dumps json response from garmin api to file for use in tests/debugging without having to call the api

ENDPOINT = GarminEndpoint.DAILY_SLEEP_SCORE
period = DatePeriod.from_last_4_weeks(time_provider.now().date())
# period = DatePeriod.from_last_7_days(time_provider.now().date())

############################################################

logging_helper.setup_logging(module_logger_name=__name__, base_log_level=logging.DEBUG)
app_config = config.get_config()
logging_helper.add_password_filter(app_config.password)

garmin_base_client = Garmin(app_config.email, app_config.password)
client = GarminApiClient(
    garmin_base_client, time_provider, app_config.session_file_path
)

client.login()

json_response = client.get_data(
    ENDPOINT,
    period,
)

save_dto_to_file(json_response, period, ENDPOINT)
