# 'garminconnect' library only supports fetching data for a single day, so we define date range endpoints and use garminconnect's internal client directly to fetch.
from datetime import date
from enum import Enum

import src.utils as utils


class GarminEndpoint(Enum):
    DAILY_SLEEP = "/wellness-service/stats/sleep/daily/{start_date}/{end_date}"
    DAILY_SLEEP_SCORE = (
        "/wellness-service/stats/daily/sleep/score/{start_date}/{end_date}"
    )
    DAILY_BB = "/wellness-service/wellness/bodyBattery/reports/daily?startDate={start_date}&endDate={end_date}"

    DAILY_RHR = "/usersummary-service/stats/heartRate/daily/{start_date}/{end_date}"
    DAILY_STEPS = "/usersummary-service/stats/steps/daily/{start_date}/{end_date}"
    DAILY_STRESS = "/usersummary-service/stats/stress/daily/{start_date}/{end_date}"

    DAILY_HRV = "/hrv-service/hrv/daily/{start_date}/{end_date}"

    # Injects start and end date into given endpoint url template
    def format(self, start_date: date, end_date: date) -> str:
        return self.value.format(
            start_date=utils.to_YYYYMMDD(start_date),
            end_date=utils.to_YYYYMMDD(end_date),
        )
