from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Generic, Sequence, TypeVar

from pydantic import TypeAdapter, ValidationError

from src.infra.garmin.garmin_api_client import JsonResponseType


@dataclass
class GarminResponseEntryDto(ABC):
    calendarDate: date


# We make the base entry covariant, such that GarminResponseDto[GarminResponseEntryDto] can be substituted with any ConcreteGarminResponseDto[ConcreteGarminResponseEntryDto]
E = TypeVar("E", bound=GarminResponseEntryDto, covariant=True)
T = TypeVar("T")


class JsonToDtoConversionError(Exception):
    pass


@dataclass
class GarminResponseDto(ABC, Generic[E]):
    entries: Sequence[E]

    @staticmethod
    @abstractmethod
    def from_json(json: JsonResponseType) -> "GarminResponseDto[E]":
        pass

    @staticmethod
    def _from_json_obj(json: JsonResponseType, dto_type: type[T]) -> T:
        adapter = TypeAdapter(dto_type)
        obj = GarminResponseDto._convert(json, adapter, dto_type)
        return obj

    @staticmethod
    def _from_json_list(json: JsonResponseType, dto_type: type[T]) -> Sequence[T]:
        adapter = TypeAdapter(Sequence[dto_type])
        obj = GarminResponseDto._convert(json, adapter, dto_type)
        return obj

    @staticmethod
    def _convert(json: JsonResponseType, adapter: TypeAdapter[T], dto_type: Any) -> T:
        try:
            obj = adapter.validate_python(json)
            return obj
        except ValidationError as e:
            custom_errors = []
            for error in e.errors():
                field = error["loc"]
                msg = error["msg"]
                type = error["type"]
                input = error["input"]
                custom_errors.append(
                    f"Error in field '{field}' of type '{type}'. Invalid value: {input}. Message: {msg}."
                )

            error_msg = (
                f"Error converting json to dto of type '{dto_type}'. Errors:\n"
                + "\n".join(custom_errors)
            )
            raise JsonToDtoConversionError(error_msg) from e
