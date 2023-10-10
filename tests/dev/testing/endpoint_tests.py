# Integration/dev testing for the endpoints
# Testcase: Request actual data from garmin and convert to DTOs

import logging
from datetime import date, timedelta

from garminconnect import Garmin  # type: ignore

from src.application.garmin_service import GarminService
from src.domain.common import DatePeriod
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.time_provider import TimeProvider
from src.setup import config, logging_helper
from tests.dev.test_utils import base_setup

logging_helper.setup_logging(module_logger_name=__name__, base_log_level=logging.DEBUG)
app_config = config.get_config()
logging_helper.add_password_filter(app_config.credentials.password)

deps = base_setup()
today = date.today()

period = DatePeriod.from_last_7_days(today)

adapter = deps.garmin_adapter

# rhr = adapter.get_daily_rhr(period)
# steps = adapter.get_daily_steps(period)
# stress = adapter.get_daily_stress(period)
# sleep = adapter.get_daily_sleep(period)
sleep_score = adapter.get_daily_sleep_score(period)
# hrv = adapter.get_daily_hrv(period)
# bb = adapter.get_daily_bb(period)

print("Done")
