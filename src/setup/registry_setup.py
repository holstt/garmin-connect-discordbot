import logging
from typing import Protocol, Sequence, cast

from typeguard import check_type

import src.presentation.metric_msg_builder as builder
from src.consts import DAYS_IN_WEEK
from src.domain.common import DatePeriod
from src.domain.metrics import (
    BodyBatteryMetrics,
    HrvMetrics,
    RhrMetrics,
    SimpleMetric,
    SleepMetrics,
    SleepScoreMetrics,
    StressMetrics,
)
from src.infra.garmin.dtos.garmin_bb_response import GarminBbResponse
from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_rhr_response import GarminRhrResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.garmin.dtos.garmin_stress_response import GarminStressResponse
from src.infra.garmin.garmin_api_client import (
    GarminApiClient,
    GarminEndpoint,
    JsonResponseType,
)
from src.infra.plotting.plotting_service import (
    create_metrics_gridplot,
    create_sleep_analysis_plot,
)
from src.setup.registry import *
from src.utils import find_first_of_type, find_first_of_type_or_fail

logger = logging.getLogger(__name__)
# TODO: Create class resp. for adding a metric to the pipeline


def build_fetcher_registry(api_client: GarminApiClient) -> FetcherRegistry:
    reg = FetcherRegistry(api_client)
    reg.register(GarminMetricId.SLEEP, build_fetcher(GarminEndpoint.DAILY_SLEEP))
    reg.register(GarminMetricId.RHR, build_fetcher(GarminEndpoint.DAILY_RHR))
    reg.register(
        GarminMetricId.SLEEP_SCORE, build_fetcher(GarminEndpoint.DAILY_SLEEP_SCORE)
    )
    reg.register(GarminMetricId.BB, build_fetcher(GarminEndpoint.DAILY_BB))
    reg.register(GarminMetricId.HRV, build_fetcher(GarminEndpoint.DAILY_HRV))
    reg.register(GarminMetricId.STRESS, build_fetcher(GarminEndpoint.DAILY_STRESS))

    return reg


def build_to_dto_converter_registry() -> ResponseToDtoConverterRegistry:
    reg = ResponseToDtoConverterRegistry()

    reg.register(
        GarminEndpoint.DAILY_SLEEP, build_to_dto_converter(GarminSleepResponse)
    )
    reg.register(GarminEndpoint.DAILY_RHR, build_to_dto_converter(GarminRhrResponse))
    reg.register(
        GarminEndpoint.DAILY_SLEEP_SCORE,
        build_to_dto_converter(GarminSleepScoreResponse),
    )
    reg.register(GarminEndpoint.DAILY_BB, build_to_dto_converter(GarminBbResponse))
    reg.register(GarminEndpoint.DAILY_HRV, build_to_dto_converter(GarminHrvResponse))
    reg.register(
        GarminEndpoint.DAILY_STRESS, build_to_dto_converter(GarminStressResponse)
    )
    return reg


def build_to_model_converter_registry() -> DtoToModelConverterRegistry:
    reg = DtoToModelConverterRegistry()

    # mapper = {
    #     GarminSleepResponse: SleepMetrics,
    #     GarminRhrResponse: RhrMetrics,
    #     GarminSleepScoreResponse: SleepScoreMetrics,
    #     GarminBbResponse: BodyBatteryMetrics,
    #     GarminHrvResponse: HrvMetrics,
    #     GarminStressResponse: StressMetrics,
    # }

    # Now iterate and register
    # for dto_type, model_type in mapper.items():
    #     reg.register(dto_type, lambda dto: model_type(dto))  # type: ignore

    reg.register(
        GarminSleepResponse, lambda dto: SleepMetrics(cast(GarminSleepResponse, dto))
    )
    reg.register(
        GarminRhrResponse, lambda dto: RhrMetrics(cast(GarminRhrResponse, dto))
    )
    reg.register(
        GarminSleepScoreResponse,
        lambda dto: SleepScoreMetrics(cast(GarminSleepScoreResponse, dto)),
    )
    reg.register(
        GarminBbResponse, lambda dto: BodyBatteryMetrics(cast(GarminBbResponse, dto))
    )
    reg.register(
        GarminHrvResponse, lambda dto: HrvMetrics(cast(GarminHrvResponse, dto))
    )
    reg.register(
        GarminStressResponse,
        lambda dto: StressMetrics(stress_data=cast(GarminStressResponse, dto)),
    )

    return reg


def build_to_presenter_converter_registry() -> ModelToVmConverterRegistry:
    reg = ModelToVmConverterRegistry()

    reg.register(
        SleepMetrics,
        lambda model: builder.sleep("Sleep", "💤", cast(SleepMetrics, model)),
    )
    reg.register(
        SleepScoreMetrics,
        lambda model: builder.metric(
            "Sleep Score", "😴", cast(SleepScoreMetrics, model), 100
        ),
    )
    reg.register(
        RhrMetrics,
        # NB: Regular heart emoji messes up the table formatting.
        lambda model: builder.metric("Resting HR", "💗", cast(RhrMetrics, model)),
    )
    reg.register(
        HrvMetrics, lambda model: builder.hrv("HRV", "💓", cast(HrvMetrics, model))
    )
    reg.register(
        BodyBatteryMetrics,
        lambda model: builder.metric(
            "Body Battery",
            "⚡",
            cast(BodyBatteryMetrics, model),
            100
            # "Body Battery", "⚡", check_type(BodyBatteryMetrics, model), 100 # check_type modifies properties of model instance, why?
        ),
    )
    reg.register(
        StressMetrics,
        lambda model: builder.metric(
            "Stress Level", "🤯", cast(StressMetrics, model), 100
        ),
    )

    return reg


def build_fetcher(endpoint: GarminEndpoint) -> Fetcher:
    def fetcher(period: DatePeriod, api_client: GarminApiClient) -> ApiResponse:
        data: JsonResponseType | None = api_client.get_data(endpoint, period)
        return ApiResponse(data, endpoint)

    return fetcher


def build_to_dto_converter(
    dto_type: type[GarminResponseDto[GarminResponseEntryDto]],
) -> ResponseToDtoConverter:
    def converter(data: JsonResponseType) -> GarminResponseDto[GarminResponseEntryDto]:
        # Create instance from static method on dto type
        return dto_type.from_json(data)

    return converter


# Build available plotting strategies.
# Each strategy checks for presence of required metrics and returns a plot if required metrics for that strategy are present
def build_plotting_strategies() -> list[PlottingStrategy]:
    def build_sleep_plot(
        metrics: Sequence[BaseMetric[GarminResponseEntryDto, Any]]
    ) -> MetricPlot | None:
        # Ensure sleep and sleep score metrics are present for this plot
        sleep = find_first_of_type(metrics, SleepMetrics)
        sleep_score = find_first_of_type(metrics, SleepScoreMetrics)

        moving_avg_window_size = DAYS_IN_WEEK  # Configurable?

        # XXX: Just viz sleep metric without score if no score available? E.g. many watches support sleep tracking but not sleep score?
        if not sleep or not sleep_score:
            logger.debug("Unable to create sleep plot, missing required metrics")
            return None

        sleep_plot = create_sleep_analysis_plot(
            sleep, sleep_score, ma_window_size=moving_avg_window_size
        )
        return MetricPlot("sleep_plot", sleep_plot)

    def build_metrics_plot(
        metrics: list[BaseMetric[GarminResponseEntryDto, Any]]
    ) -> MetricPlot:
        days_to_plot = DAYS_IN_WEEK  # Configurable?
        # No specific metrics required, it's just a generic plot of all metrics
        metrics_plot = create_metrics_gridplot(metrics, n=days_to_plot)
        return MetricPlot("metrics_plot", metrics_plot)

    return [build_sleep_plot, build_metrics_plot]
