# Integration/dev testing for the endpoints
# Testcase: Request actual data from garmin and convert to DTOs

import logging
from datetime import timedelta

from garminconnect import Garmin  # type: ignore

from src import config, logging_helper
from src.application.garmin_service import GarminService
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.time_provider import TimeProvider

logging_helper.setup_logging(module_logger_name=__name__, base_log_level=logging.DEBUG)
app_config = config.get_config()
logging_helper.add_password_filter(app_config.password)

time_provider = TimeProvider()

garmin_base_client = Garmin(app_config.email, app_config.password)

garmin_client = GarminApiClient(
    garmin_base_client, time_provider, app_config.session_file_path
)
adapter = GarminApiAdapter(garmin_client)
service = GarminService(adapter)

garmin_client.login()

end_date = time_provider.now().date()
start_date = end_date - timedelta(days=6)

# rhr = adapter.get_daily_rhr(start_date, end_date)
# steps = adapter.get_daily_steps(start_date, end_date)
# stress = adapter.get_daily_stress(start_date, end_date)
# sleep = adapter.get_daily_sleep(start_date, end_date)
sleep_score = adapter.get_daily_sleep_score(start_date, end_date)
# hrv = adapter.get_daily_hrv(start_date, end_date)
# bb = adapter.get_daily_bb(start_date, end_date)

print("Done")
