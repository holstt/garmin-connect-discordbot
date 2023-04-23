import logging
from abc import ABC
from datetime import date, datetime, timedelta
from typing import Any, Optional, Union

from src.domain.models import HealthSummary, HrvMetrics, SleepMetrics, SleepScoreMetrics
from src.infra.garmin_api_client import GarminApiAdapter, GarminApiClient
from src.infra.garmin_dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin_dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin_dtos.garmin_sleep_score_response import GarminSleepScoreResponse

logger = logging.getLogger(__name__)


from typing import Callable, Optional, TypeVar

T = TypeVar(
    "T", bound=Union[GarminSleepResponse, GarminHrvResponse, GarminSleepScoreResponse]
)


class GarminService:
    def __init__(self, client: GarminApiAdapter):
        self._client = client

    # Returns health stats for the past 7 days (including end date) or None if today has not been registered yet for one of the metrics
    def try_get_weekly_health_summary(self, week_end: date) -> Optional[HealthSummary]:
        # Get start of week range
        week_start = week_end - timedelta(days=7)

        # Try to get weekly metrics
        return self._try_get_summary(week_start, week_end)

    def _try_get_summary(
        self, week_start: date, week_end: date
    ) -> Optional[HealthSummary]:
        # Get each metric and ensure that today is in the data

        # Get sleep data
        weekly_sleep = self._get_data(
            week_start, week_end, self._client.get_daily_sleep
        )
        if not weekly_sleep:
            return None

        # Get HRV data
        weekly_hrv = self._get_data(week_start, week_end, self._client.get_daily_hrv)
        if not weekly_hrv:
            return None

        # Get sleep score data
        weekly_sleep_score = self._get_data(
            week_start, week_end, self._client.get_daily_sleep_score
        )
        if not weekly_sleep_score:
            return None

        # Create metrics objects
        sleep_metrics = SleepMetrics(sleep_data=weekly_sleep)
        hrv_metrics = HrvMetrics(hrv_data=weekly_hrv)
        sleep_score_metrics = SleepScoreMetrics(sleep_data=weekly_sleep_score)

        # Create health summary
        health_summary = HealthSummary(
            date=week_end,
            sleep=sleep_metrics,
            hrv=hrv_metrics,
            sleep_score=sleep_score_metrics,
        )

        return health_summary

    def _get_data(
        self,
        start_date: date,
        end_date: date,
        get_fn: Callable[[date, date], T],
    ) -> Optional[T]:
        data: Optional[T] = get_fn(start_date, end_date)
        if end_date not in [x.calendar_date.date() for x in data.entries]:
            logger.info(
                f"Did not find {get_fn.__name__} data for specified end date: {end_date.isoformat()}"
            )
            return None
        return data
