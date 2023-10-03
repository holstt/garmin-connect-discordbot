import logging
from datetime import date
from typing import Optional, Union

import src.domain.models as models
import src.infra.garmin.dtos as dtos
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter

logger = logging.getLogger(__name__)


from datetime import date
from typing import Callable, Optional, TypeVar

# XXX: Avoid union type by using a protocol
T = TypeVar(
    "T",
    bound=Union[
        dtos.GarminSleepResponse,
        dtos.GarminHrvResponse,
        dtos.GarminSleepScoreResponse,
        dtos.GarminRhrResponse,
    ],
)


class GarminService:
    def __init__(self, client: GarminApiAdapter):
        self._client = client

    # Returns health stats for the past 7 days (including end date) or None if today has not been registered yet for one of the metrics
    def try_get_weekly_health_summary(
        self, week_end: date
    ) -> Optional[models.HealthSummary]:
        # Get start of week range
        period = models.DatePeriod.from_last_7_days(week_end)

        # Try to get weekly metrics
        return self._try_get_summary(period)

    def _try_get_summary(
        self, period: models.DatePeriod
    ) -> Optional[models.HealthSummary]:
        # Get each metric and ensure that today is in the data
        # Early return in case of missing data to avoid unnecessary requests
        # XXX: Consider that all metrics are available for the same dates, maybe just request all and check. Such that code can be simplified

        # Get RHR data
        dto_rhr = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_rhr
        )
        if not dto_rhr:
            return None

        # Get HRV data
        dto_hrv = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_hrv
        )
        if not dto_hrv:
            return None

        # Get sleep data
        dto_sleep = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_sleep
        )
        if not dto_sleep:
            return None

        # Get sleep score data
        dto_sleep_score = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_sleep_score
        )
        if not dto_sleep_score:
            return None

        # Create health summary
        health_summary = models.HealthSummary(
            date=period.end,
            sleep=models.SleepMetrics(sleep_data=dto_sleep),
            hrv=models.HrvMetrics(hrv_data=dto_hrv),
            sleep_score=models.SleepScoreMetrics(sleep_data=dto_sleep_score),
            rhr=models.RhrMetrics(rhr_data=dto_rhr),
        )

        return health_summary

    def _get_and_ensure_includes_period_end(
        self,
        period: models.DatePeriod,
        get_data_fn: Callable[[models.DatePeriod], T],
    ) -> Optional[T]:
        # Try get data for period
        data: Optional[T] = get_data_fn(period)

        # Ensure that the data includes the end date
        if period.end not in [x.calendarDate for x in data.entries]:
            logger.info(
                f"Did not find {get_data_fn.__name__} data for specified end date: {period.end.isoformat()}"
            )
            return None
        return data
