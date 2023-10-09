import logging
from datetime import date
from typing import Optional

import src.domain.metrics as metrics
from src.domain.common import DatePeriod
from src.infra.garmin.dtos import *
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.plotting.plotting_service import (
    create_metrics_gridplot,
    create_sleep_analysis_plot,
)
from src.registry import *
from src.utils import find_first_of_type_or_fail

logger = logging.getLogger(__name__)


from datetime import date
from typing import Optional

DAYS_IN_WEEK = 7


class GarminService:
    def __init__(
        self,
        client: GarminApiAdapter,
        fetcher_registry: FetcherRegistry,
        response_to_dto_converter_registry: ResponseToDtoConverterRegistry,
        dto_to_model_converter_registry: DtoToModelConverterRegistry,
    ):
        super().__init__()
        self._client = client
        self._fetcher_registry = fetcher_registry
        self._response_to_dto_converter_registry = response_to_dto_converter_registry
        self._dto_to_model_converter_registry = dto_to_model_converter_registry

    # Returns health stats for the past 7 days (including end date)
    # or None if today has not been registered yet for one of the metrics
    def try_get_weekly_health_summary(
        self, week_end: date
    ) -> Optional[metrics.HealthSummary]:
        # 4 weeks of data needed for the summary if includes plots
        period = DatePeriod.from_last_4_weeks(week_end)
        # period = DatePeriod.from_last_7_days(week_end)

        # Try to get weekly metrics
        return self._try_get_summary(period)

    def _try_get_summary(self, period: DatePeriod) -> Optional[metrics.HealthSummary]:
        # NB: Metrics obtained while sleeping most likely to be missing in today's data (e.g. if no sleep registered yet, or if not wearing device during sleep). Should be requested first to avoid unnecessary requests
        # TODO: Inject metrics to include
        metrics_to_include = [metric for metric in GarminMetricId]

        dtos: list[GarminResponseDto[GarminResponseEntryDto]] = []
        for metric in metrics_to_include:
            # Fetch this metric data
            response = self._fetcher_registry.fetch(metric, period)

            # Early return in case of missing data to avoid additional requests
            if not response.data:
                logger.info(f"Empty data for {metric}. Summary will not be generated.")
                return None

            dto = self._response_to_dto_converter_registry.convert(
                response.endpoint, response.data
            )

            logger.info(f"Got {metric} data with num entries: {len(dto.entries)}")

            # Ensure that the data includes the end date
            if period.end not in [x.calendarDate for x in dto.entries]:
                logger.info(
                    f"Did not find {metric} data for specified end date: {period.end.isoformat()}. Summary will not be generated."
                )
                return None

            dtos.append(dto)

        # Iterate dtos and convert to models
        models: list[BaseMetric[GarminResponseEntryDto, Any]] = []
        for dto in dtos:
            model = self._dto_to_model_converter_registry.convert(dto)
            models.append(model)

        # Create health summary
        health_summary = metrics.HealthSummary(
            date=period.end,
            metrics=models,
        )

        return health_summary
