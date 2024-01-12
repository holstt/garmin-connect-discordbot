from typing import Any, Callable, Generic, NamedTuple, Sequence, TypeVar

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
from src.presentation.view_models import MetricPlot, MetricViewModel
from src.setup.garmin_metrid_ids import GarminMetricId

# from src.setup.init_factories import ResponseToDtoConverter

# TODO: Create all registries from generic registry class


class ApiResponse(NamedTuple):
    data: JsonResponseType | None
    endpoint: GarminEndpoint


T = TypeVar("T")  # Input type
U = TypeVar("U")  # Output type
Converter = Callable[[T], U]

K = TypeVar("K")  # Key type
V = TypeVar("V")  # Value type


# Factory as a dict wrapper for safe access
class Factory(Generic[K, V]):
    def __init__(self):
        super().__init__()
        self._values: dict[K, V] = {}

    def register(self, key: K, value: V):
        if key in self._values:
            raise ValueError(f"Factory already contains key: {key}")
        self._values[key] = value

    def remove(self, key: K):
        if key not in self._values:
            raise ValueError(f"Factory does not contain key: {key}")
        del self._values[key]

    def get(self, key: K) -> V:
        if key not in self._values:
            raise ValueError(f"Factory does not contain key: {key}")
        val = self._values[key]
        return val


# Factory types
ResponseToDtoConverter = Callable[
    [JsonResponseType], GarminResponseDto[GarminResponseEntryDto]
]
Fetcher = Callable[[DatePeriod], ApiResponse]


# class FetcherRegistry:
#     def __init__(self, api_client: GarminApiClient):
#         super().__init__()
#         self._fetchers: dict[GarminMetricId, Fetcher] = {}
#         self._client = api_client

#     def register(self, id: GarminMetricId, fetcher: Fetcher):
#         self._fetchers[id] = fetcher

#     def fetch(self, id: GarminMetricId, period: DatePeriod) -> ApiResponse:
#         if id not in self._fetchers:
#             raise ValueError(f"No fetcher found for {id}")
#         func = self._fetchers[id]
#         return func(period, self._client)


class Registry(Generic[T, U]):
    def __init__(self):
        super().__init__()
        self._converters: dict[type[T], Converter[T, U]] = {}

    def register(self, input_type: type[T], converter: Converter[T, U]):
        self._converters[input_type] = converter

    def convert(self, instance: T) -> U:
        instance_type = type(instance)
        if instance_type not in self._converters:
            raise ValueError(f"No converter found for {instance_type}")
        func = self._converters[instance_type]
        return func(instance)


# class ResponseToDtoConverterRegistry:
#     def __init__(self):
#         super().__init__()
#         self._converters: dict[GarminEndpoint, ResponseToDtoConverter] = {}

#     def register(self, endpoint: GarminEndpoint, converter: ResponseToDtoConverter):
#         self._converters[endpoint] = converter

#     def convert(
#         self, endpoint: GarminEndpoint, data: JsonResponseType
#     ) -> GarminResponseDto[GarminResponseEntryDto]:
#         if endpoint not in self._converters:
#             raise ValueError(f"No converter found for {endpoint}")
#         func = self._converters[endpoint]
#         return func(data)


DtoToModelConverterRegistry = Registry[
    GarminResponseDto[GarminResponseEntryDto], BaseMetric[GarminResponseEntryDto, Any]
]


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
    [Sequence[BaseMetric[GarminResponseEntryDto, Any]]], MetricPlot | None
]

DtoToModelConverter = Callable[
    [GarminResponseDto[GarminResponseEntryDto]], BaseMetric[GarminResponseEntryDto, Any]
]


# class CentralizedRegistry(NamedTuple):
#     fetcher_registry: FetcherRegistry
#     response_to_dto_converter_registry: ResponseToDtoConverterRegistry
#     dto_to_model_converter_registry: DtoToModelConverterRegistry
#     model_to_vm_converter_registry: ModelToVmConverterRegistry


# XXX: Registry ensure all required components registered for a metric (not used atm)
# class CentralizedRegistryBuilder:
#     def __init__(self, api_client: GarminApiClient):
#         super().__init__()
#         self._fetcher_registry = FetcherRegistry(api_client)
#         self._response_to_dto_converter_registry = ResponseToDtoConverterRegistry()
#         self._dto_to_model_converter_registry = DtoToModelConverterRegistry()
#         self._model_to_vm_converter_registry = ModelToVmConverterRegistry()
# Add entire metric pipeline
#     def add_metric(
#         self,
#         metric_id: GarminMetricId,
#         fetcher: Fetcher,
#         endpoint: GarminEndpoint,
#         response_to_dto_converter: ResponseToDtoConverter,
#         dto_type: type[GarminResponseDto[GarminResponseEntryDto]],
#         dto_to_model_converter: DtoToModelConverter,
#         model_type: type[BaseMetric[GarminResponseEntryDto, Any]],
#         model_to_vm_converter: ModelToVmConverter,
#     ) -> "CentralizedRegistryBuilder":
#         self._fetcher_registry.register(metric_id, fetcher)
#         self._response_to_dto_converter_registry.register(
#             endpoint, response_to_dto_converter
#         )
#         self._dto_to_model_converter_registry.register(dto_type, dto_to_model_converter)
#         self._model_to_vm_converter_registry.register(model_type, model_to_vm_converter)
#         return self

#     def build(self) -> CentralizedRegistry:
#         # XXX: Any validation?

#         return CentralizedRegistry(
#             self._fetcher_registry,
#             self._response_to_dto_converter_registry,
#             self._dto_to_model_converter_registry,
#             self._model_to_vm_converter_registry,
#         )
