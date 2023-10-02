import logging
from datetime import date, timedelta
from typing import Optional, Union

from src.domain.models import (DatePeriod, HealthSummary, HrvMetrics,
                               SleepMetrics, SleepScoreMetrics)
from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import \
    GarminSleepScoreResponse
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter

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
        period = DatePeriod.from_last_7_days(week_end)

        # Try to get weekly metrics
        return self._try_get_summary(period)

    def _try_get_summary(
        self, period: DatePeriod
    ) -> Optional[HealthSummary]:
        # Get each metric and ensure that today is in the data

        # Get HRV data
        weekly_hrv = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_hrv
        )
        if not weekly_hrv:
            return None

        # Get sleep data
        weekly_sleep = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_sleep
        )
        if not weekly_sleep:
            return None

        # Get sleep score data
        weekly_sleep_score = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_sleep_score
        )
        if not weekly_sleep_score:
            return None

        # Create metrics objects
        sleep_metrics = SleepMetrics(sleep_data=weekly_sleep)
        hrv_metrics = HrvMetrics(hrv_data=weekly_hrv)
        sleep_score_metrics = SleepScoreMetrics(sleep_data=weekly_sleep_score)

        # Create health summary
        health_summary = HealthSummary(
            date=period.end,
            sleep=sleep_metrics,
            hrv=hrv_metrics,
            sleep_score=sleep_score_metrics,
        )

        return health_summary

    def _get_and_ensure_includes_period_end(
        self,
        period: DatePeriod,
        get_fn: Callable[[DatePeriod], T],
    ) -> Optional[T]:
        data: Optional[T] = get_fn(period)
        if period.end not in [x.calendarDate for x in data.entries]:
            logger.info(
                f"Did not find {get_fn.__name__} data for specified end date: {period.end.isoformat()}"
            )
            return None
        return data
