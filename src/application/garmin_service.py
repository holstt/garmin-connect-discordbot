import logging
from datetime import date, datetime, timedelta
from typing import Any, Optional

from src.domain.models import HealthSummary, HrvMetrics, SleepMetrics
from src.infra.garmin_api_client import GarminApiClient
from src.infra.garmin_dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin_dtos.garmin_sleep_response import GarminSleepResponse

logger = logging.getLogger(__name__)


class GarminService:
    def __init__(self, client: GarminApiClient):
        self._client = client

    # Returns health stats for the past 7 days (including end date) or None if today has not been registered yet
    def try_get_weekly_health_summary(self, week_end: date) -> Optional[HealthSummary]:
        # Get start of week range
        week_start: date = week_end - timedelta(days=7)

        # Get sleep data
        weekly_sleep: GarminSleepResponse = self._client.get_daily_sleep(
            start_date=week_start, end_date=week_end
        )
        # Ensure that today is in the data
        if week_end not in [x.calendar_date.date() for x in weekly_sleep.entries]:
            logger.info(
                "Did not find sleep data for specified end date: "
                + week_end.isoformat()
            )
            return None

        # Get hrv data
        weekly_hrv: GarminHrvResponse = self._client.get_daily_hrv(
            start_date=week_start, end_date=week_end
        )

        # Ensure that today is in the data
        if week_end not in [x.calendar_date.date() for x in weekly_hrv.hrv_summaries]:
            logger.info(
                "Did not find hrv data for specified end date: " + week_end.isoformat()
            )
            return None

        sleep_metrics: SleepMetrics = SleepMetrics(sleep_data=weekly_sleep)
        hrv_metrics: HrvMetrics = HrvMetrics(hrv_data=weekly_hrv)

        # Create health summary
        health_summary: HealthSummary = HealthSummary(
            date=week_end,
            sleep=sleep_metrics,
            hrv=hrv_metrics,
        )

        return health_summary
