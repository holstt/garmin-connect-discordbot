import logging
from datetime import date
from typing import Optional, Sequence

import src.domain.metrics as metrics
from src.domain.common import DatePeriod
from src.infra.garmin.dtos import *
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.setup.garmin_metrid_ids import GarminMetricId
from src.setup.factories import *

logger = logging.getLogger(__name__)


from datetime import date
from typing import Optional


class GarminService:
    def __init__(
        self,
        client: GarminApiClient,
        fetcher_factory: Factory[GarminMetricId, Fetcher],
        response_to_dto_converter_factory: Factory[
            GarminEndpoint, ResponseToDtoConverter
        ],
        dto_to_model_converter_registry: DtoToModelConverterRegistry,
        metrics_to_include: Sequence[GarminMetricId],
    ):
        super().__init__()
        self._client = client
        self._fetcher_factory = fetcher_factory
        self._response_to_dto_converter_factory = response_to_dto_converter_factory
        self._dto_to_model_converter_registry = dto_to_model_converter_registry
        self._metrics_to_include = metrics_to_include

    # Returns health summary
    # or None if today has not been registered yet for one of the metrics
    def try_get_health_summary(self, end_date: date) -> Optional[metrics.HealthSummary]:
        # Request 4 weeks of data -> needed for the summary (if includes plots)
        period = DatePeriod.from_last_4_weeks(end_date)
        # period = DatePeriod.from_last_7_days(week_end)

        # Try to get summary for this period
        return self._try_get_health_summary(period)

    def _try_get_health_summary(
        self, period: DatePeriod
    ) -> Optional[metrics.HealthSummary]:
        logger.info(f"Trying to create health summary for period: {period}")

        dtos: Sequence[GarminResponseDto[GarminResponseEntryDto]] = []

        # TODO: Move to separate method, fetch_metrics(), fetch_metric()
        for metric in self._metrics_to_include:
            # Fetch this metric data
            fetcher = self._fetcher_factory.get(metric)
            response = fetcher(period, self._client)
            # response = self._fetcher_factory.fetch(metric, period)

            # Early return in case of missing data to avoid additional requests
            if not response.data:
                # XXX: Is this unexpected? Throw exception?
                logger.info(
                    f"Empty response for {metric}. Summary will not be generated."
                )
                return None

            convert_to_dto_func = self._response_to_dto_converter_factory.get(
                response.endpoint
            )
            dto = convert_to_dto_func(response.data)

            logger.debug(f"Got {metric} data with num entries: {len(dto.entries)}")

            # Ensure that the data includes the end date
            if period.end not in [x.calendarDate for x in dto.entries]:
                logger.info(
                    f"{metric} data did contain entry for the target end date: {period.end.isoformat()}. Summary will not be generated."
                )
                return None

            dtos.append(dto)

        # Iterate dtos and convert to models
        # TODO: Move to separate method, convert_to_models()
        models: Sequence[BaseMetric[GarminResponseEntryDto, Any]] = []
        for dto in dtos:
            model = self._dto_to_model_converter_registry.convert(dto)
            models.append(model)

        # Create health summary
        health_summary = metrics.HealthSummary(
            date=period.end,
            metrics=models,
        )

        logger.info(f"Health summary for period created.")
        return health_summary
