from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Generic, Protocol, TypeVar, cast

from pydantic import TypeAdapter

from src.infra.garmin.garmin_api_client import JsonResponseType


@dataclass
class GarminResponseEntryDto(ABC):
    calendarDate: date


# We make the base entry covariant, such that GarminResponseDto[GarminResponseEntryDto] can be substituted with any ConcreteGarminResponseDto[ConcreteGarminResponseEntryDto]
E = TypeVar("E", bound=GarminResponseEntryDto, covariant=True)
T = TypeVar("T")


@dataclass
class GarminResponseDto(ABC, Generic[E]):
    entries: list[E]

    @staticmethod
    @abstractmethod
    def from_json(json: JsonResponseType) -> "GarminResponseDto[E]":
        pass

    @staticmethod
    def _from_json_obj(json: JsonResponseType, dto_type: type[T]) -> T:
        adapter = TypeAdapter(dto_type)
        obj = adapter.validate_python(json)
        return obj

    @staticmethod
    def _from_json_list(json: JsonResponseType, dto_type: type[T]) -> list[T]:
        adapter = TypeAdapter(list[dto_type])
        obj = adapter.validate_python(json)
        return obj
