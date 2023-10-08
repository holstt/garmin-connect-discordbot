from enum import Enum
from typing import Any, Callable, NamedTuple

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
from src.presentation.metric_msg_builder import MetricViewModel


class GarminMetricId(Enum):
    SLEEP = "sleep"
    SLEEP_SCORE = "sleep_score"
    RHR = "rhr"
    BB = "bb"
    HRV = "hrv"
    STRESS = "stress"
    # STEPS = "steps"


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


DtoToConverterModel = Callable[
    [GarminResponseDto[GarminResponseEntryDto]], BaseMetric[Any]
]


class DtoToModelConverterRegistry:
    def __init__(self):
        super().__init__()
        self._converters: dict[
            type[GarminResponseDto[GarminResponseEntryDto]], DtoToConverterModel
        ] = {}

    def register(
        self,
        dto_type: type[GarminResponseDto[GarminResponseEntryDto]],
        converter: DtoToConverterModel,
    ):
        self._converters[dto_type] = converter

    def convert(self, instance: GarminResponseDto[GarminResponseEntryDto]):
        instance_type = type(instance)
        if instance_type not in self._converters:
            raise ValueError(f"No converter found for {instance_type}")
        func = self._converters[instance_type]
        return func(instance)


ModelToPresenterConverter = Callable[[BaseMetric[Any]], MetricViewModel]


class ModelToPresenterConverterRegistry:
    def __init__(self):
        super().__init__()
        self._converters: dict[type[BaseMetric[Any]], ModelToPresenterConverter] = {}

    def register(
        self, instance: type[BaseMetric[Any]], converter: ModelToPresenterConverter
    ):
        self._converters[instance] = converter

    def convert(self, instance: BaseMetric[Any]):
        instance_type = type(instance)
        if instance_type not in self._converters:
            raise ValueError(f"No converter found for {instance_type}")
        func = self._converters[instance_type]
        return func(instance)
