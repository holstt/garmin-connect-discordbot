import logging
from datetime import date
from typing import Optional, Union

import src.domain.metrics as metrics
import src.infra.garmin.dtos as dtos
from src.domain.common import DatePeriod
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.plotting.metrics_plot import MetricsData
from src.infra.plotting.plotting_service import create_metrics_plot, create_sleep_plot

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
        dtos.GarminBbResponse,
        dtos.GarminStressResponse,
    ],
)

DAYS_IN_WEEK = 7


class GarminService:
    def __init__(self, client: GarminApiAdapter):
        self._client = client

    # Returns health stats for the past 7 days (including end date) or None if today has not been registered yet for one of the metrics
    def try_get_weekly_health_summary(
        self, week_end: date
    ) -> Optional[metrics.HealthSummary]:
        # 4 weeks of data needed for the summary if includes plots
        period = DatePeriod.from_last_4_weeks(week_end)
        # period = DatePeriod.from_last_7_days(week_end)

        # Try to get weekly metrics
        return self._try_get_summary(period)

    def _try_get_summary(self, period: DatePeriod) -> Optional[metrics.HealthSummary]:
        # Get each metric and ensure that today is in the data
        # Early return in case of missing data to avoid unnecessary requests
        # XXX: Consider that all metrics are available for the same dates, maybe just request all and check. Such that code can be simplified

        # NB: Metrics obtained while sleeping most likely to be missing in today's data (e.g. if no sleep registered yet, or if not wearing device during sleep)

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

        # Get RHR data
        dto_rhr = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_rhr
        )
        if not dto_rhr:
            return None

        dto_bb = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_bb
        )
        if not dto_bb:
            return None

        dto_stress = self._get_and_ensure_includes_period_end(
            period, self._client.get_daily_stress
        )
        if not dto_stress:
            return None

        # Create metrics plot for weekly period
        metrics_plot = create_metrics_plot(
            MetricsData(
                sleep=dto_sleep,
                sleep_score=dto_sleep_score,
                bb=dto_bb,
                rhr=dto_rhr,
                stress=dto_stress,
                hrv=dto_hrv,
                # steps=None,
            ).get_last_n(DAYS_IN_WEEK)
        )

        # Create sleep plot for full period
        sleep_plot = create_sleep_plot(
            dto_sleep, dto_sleep_score, ma_window_size=DAYS_IN_WEEK
        )

        # Create health summary
        health_summary = metrics.HealthSummary(
            date=period.end,
            sleep=metrics.SleepMetrics(sleep_data=dto_sleep),
            hrv=metrics.HrvMetrics(hrv_data=dto_hrv),
            sleep_score=metrics.SleepScoreMetrics(sleep_data=dto_sleep_score),
            rhr=metrics.RhrMetrics(rhr_data=dto_rhr),
            bb=metrics.BodyBatteryMetrics(bb_data=dto_bb),
            stress=metrics.StressMetrics(stress_data=dto_stress),
            metrics_plot=metrics_plot,
            sleep_plot=sleep_plot,
        )

        return health_summary

    def _get_and_ensure_includes_period_end(
        self,
        period: DatePeriod,
        get_data_fn: Callable[[DatePeriod], Optional[T]],
    ) -> Optional[T]:
        # Try get data for period
        data = get_data_fn(period)

        if not data:
            logger.info(f"Empty data for {get_data_fn.__name__}")
            return None

        logger.info(
            f"Got {get_data_fn.__name__} data with num entries: {len(data.entries)}"
        )

        # Ensure that the data includes the end date
        if period.end not in [x.calendarDate for x in data.entries]:
            logger.info(
                f"Did not find {get_data_fn.__name__} data for specified end date: {period.end.isoformat()}"
            )
            return None
        return data
