import logging
from typing import Sequence, cast

from discord_webhook import DiscordEmbed

import src.presentation.view_models as view_models
from src.consts import DAYS_IN_WEEK
from src.domain.common import DatePeriod
from src.domain.metrics import (
    BbMetrics,
    HrvMetrics,
    RhrMetrics,
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
from src.presentation.discord_messages import DiscordMessageLines, DiscordMessageTable
from src.setup.message_formats import MessageFormat
from src.setup.registry import *
from src.utils import find_first_of_type

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
    reg.register(GarminBbResponse, lambda dto: BbMetrics(cast(GarminBbResponse, dto)))
    reg.register(
        GarminHrvResponse, lambda dto: HrvMetrics(cast(GarminHrvResponse, dto))
    )
    reg.register(
        GarminStressResponse,
        lambda dto: StressMetrics(stress_data=cast(GarminStressResponse, dto)),
    )

    return reg


def build_to_vm_converter_registry() -> ModelToVmConverterRegistry:
    reg = ModelToVmConverterRegistry()

    reg.register(
        SleepMetrics,
        lambda model: view_models.sleep_message(
            "Sleep", "💤", cast(SleepMetrics, model)
        ),
    )
    reg.register(
        SleepScoreMetrics,
        lambda model: view_models.metric_message(
            "Sleep Score", "😴", cast(SleepScoreMetrics, model), 100
        ),
    )
    reg.register(
        RhrMetrics,
        # NB: Regular heart emoji messes up the table formatting.
        lambda model: view_models.metric_message(
            "Resting HR", "💗", cast(RhrMetrics, model)
        ),
    )
    reg.register(
        HrvMetrics,
        lambda model: view_models.hrv_message("HRV", "💓", cast(HrvMetrics, model)),
    )
    reg.register(
        BbMetrics,
        lambda model: view_models.metric_message(
            "Body Battery",
            "⚡",
            cast(BbMetrics, model),
            100
            # "Body Battery", "⚡", check_type(BodyBatteryMetrics, model), 100 # check_type modifies properties of model instance, why?
        ),
    )
    reg.register(
        StressMetrics,
        lambda model: view_models.metric_message(
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
def build_plotting_strategies() -> Sequence[PlottingStrategy]:
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
        metrics: Sequence[BaseMetric[GarminResponseEntryDto, Any]]
    ) -> MetricPlot:
        days_to_plot = DAYS_IN_WEEK  # Configurable?
        # No specific metrics required, it's just a generic plot of all metrics
        metrics_plot = create_metrics_gridplot(metrics, n=days_to_plot)
        return MetricPlot("metrics_plot", metrics_plot)

    return [build_sleep_plot, build_metrics_plot]


MessageStrategy = Callable[[view_models.HealthSummaryViewModel], DiscordEmbed]


def build_message_strategy(message_format: MessageFormat) -> MessageStrategy:
    match message_format:
        case MessageFormat.LINES:
            return lambda vm: DiscordMessageLines(vm)
        case MessageFormat.TABLE:
            return lambda vm: DiscordMessageTable(vm)
