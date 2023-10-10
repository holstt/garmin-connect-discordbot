from enum import Enum
from typing import Any, Callable, NamedTuple, TypeVar

from src.domain.common import DatePeriod
from src.domain.metrics import BaseMetric
from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import (
    GarminApiClient,
    GarminEndpoint,
    JsonResponseType,
)
from src.presentation.metric_msg_builder import MetricPlot, MetricViewModel
from src.setup.garmin_metrid_ids import GarminMetricId

# Unique identifier for each Garmin metric.
# Order determines: the order in which metrics are fetched and the order which metrics are displayed
# NB: Metrics obtained while sleeping most likely to be missing in today's data (e.g. if no sleep registered yet, or if not wearing device during sleep). Should be requested first to avoid unnecessary requests


class ApiResponse(NamedTuple):
    data: JsonResponseType | None
    endpoint: GarminEndpoint


Fetcher = Callable[[DatePeriod, GarminApiClient], ApiResponse]


class FetcherRegistry:
    def __init__(self, api_client: GarminApiClient):
        super().__init__()
        self._fetchers: dict[GarminMetricId, Fetcher] = {}
        self._client = api_client

    def register(self, id: GarminMetricId, fetcher: Fetcher):
        self._fetchers[id] = fetcher

    def fetch(self, id: GarminMetricId, period: DatePeriod) -> ApiResponse:
        if id not in self._fetchers:
            raise ValueError(f"No fetcher found for {id}")
        func = self._fetchers[id]
        return func(period, self._client)


ResponseToDtoConverter = Callable[
    [JsonResponseType], GarminResponseDto[GarminResponseEntryDto]
]


class ResponseToDtoConverterRegistry:
    def __init__(self):
        super().__init__()
        self._converters: dict[GarminEndpoint, ResponseToDtoConverter] = {}

    def register(self, endpoint: GarminEndpoint, converter: ResponseToDtoConverter):
        self._converters[endpoint] = converter

    def convert(
        self, endpoint: GarminEndpoint, data: JsonResponseType
    ) -> GarminResponseDto[GarminResponseEntryDto]:
        if endpoint not in self._converters:
            raise ValueError(f"No converter found for {endpoint}")
        func = self._converters[endpoint]
        return func(data)


DtoToModelConverter = Callable[
    [GarminResponseDto[GarminResponseEntryDto]], BaseMetric[GarminResponseEntryDto, Any]
]


class DtoToModelConverterRegistry:
    def __init__(self):
        super().__init__()
        self._converters: dict[
            type[GarminResponseDto[GarminResponseEntryDto]], DtoToModelConverter
        ] = {}

    def register(
        self,
        dto_type: type[GarminResponseDto[GarminResponseEntryDto]],
        converter: DtoToModelConverter,
    ):
        self._converters[dto_type] = converter

    def convert(self, instance: GarminResponseDto[GarminResponseEntryDto]):
        instance_type = type(instance)
        if instance_type not in self._converters:
            raise ValueError(f"No converter found for {instance_type}")
        func = self._converters[instance_type]
        return func(instance)


ModelToVmConverter = Callable[
    [BaseMetric[GarminResponseEntryDto, Any]], MetricViewModel
]


class ModelToVmConverterRegistry:
    def __init__(self):
        super().__init__()
        self._converters: dict[
            type[BaseMetric[GarminResponseEntryDto, Any]], ModelToVmConverter
        ] = {}

    def register(
        self,
        key: type[BaseMetric[GarminResponseEntryDto, Any]],
        converter: ModelToVmConverter,
    ):
        self._converters[key] = converter

    def convert(
        self, instance: BaseMetric[GarminResponseEntryDto, Any]
    ) -> MetricViewModel:
        instance_type = type(instance)
        if instance_type not in self._converters:
            raise ValueError(f"No converter found for {instance_type}")
        func = self._converters[instance_type]
        return func(instance)


# Given a list of models, return a plot if required metrics are available, otherwise None
PlottingStrategy = Callable[
    [list[BaseMetric[GarminResponseEntryDto, Any]]], MetricPlot | None
]
