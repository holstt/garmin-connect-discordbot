# from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, TypeAdapter

T = TypeVar("T")


class GarminDto(Generic[T]):
    @staticmethod
    def from_json(json: Any) -> T:
        raise NotImplementedError()


# If no duration in stress segment, value will be none
class StressValues(BaseModel):
    highStressDuration: Optional[int]
    lowStressDuration: Optional[int]
    overallStressLevel: int
    restStressDuration: Optional[int]
    mediumStressDuration: Optional[int]


class StressEntry(BaseModel):
    calendarDate: date
    values: StressValues


@dataclass
class GarminStressResponse(GarminDto["GarminStressResponse"]):
    entries: list[StressEntry]

    @staticmethod
    def from_json(json: Any) -> "GarminStressResponse":
        adapter = TypeAdapter(list[StressEntry])
        entries = adapter.validate_python(json)
        return GarminStressResponse(entries)
