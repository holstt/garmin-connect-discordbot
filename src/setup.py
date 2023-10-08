from abc import ABC
from enum import Enum
from typing import Any, Callable, NamedTuple, Optional, Protocol, Type, TypeVar

from src.domain.common import DatePeriod
from src.domain.metrics import BaseMetric
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
from src.presentation.metric_msg_builder import MetricViewModel
from src.registry import *

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

    reg.register(GarminEndpoint.DAILY_SLEEP, build_converter(GarminSleepResponse))
    reg.register(GarminEndpoint.DAILY_RHR, build_converter(GarminRhrResponse))
    reg.register(
        GarminEndpoint.DAILY_SLEEP_SCORE, build_converter(GarminSleepScoreResponse)
    )
    reg.register(GarminEndpoint.DAILY_BB, build_converter(GarminBbResponse))
    reg.register(GarminEndpoint.DAILY_HRV, build_converter(GarminHrvResponse))
    reg.register(GarminEndpoint.DAILY_STRESS, build_converter(GarminStressResponse))
    reg.register(GarminEndpoint.DAILY_RHR, build_converter(GarminRhrResponse))
    return reg


def build_fetcher(endpoint: GarminEndpoint) -> Fetcher:
    def fetcher(period: DatePeriod, api_client: GarminApiClient) -> ApiResponse:
        data: JsonResponseType | None = api_client.get_data(endpoint, period)
        return ApiResponse(data, endpoint)

    return fetcher


def build_converter(
    dto_type: type[GarminResponseDto[GarminResponseEntryDto]],
) -> ResponseToDtoConverter:
    def converter(data: JsonResponseType) -> Any:
        # Create instance from static method on dto type
        return dto_type.from_json(data)

    return converter
