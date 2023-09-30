from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, TypeAdapter


class StressValues(BaseModel):
    highStressDuration: int
    lowStressDuration: int
    overallStressLevel: int
    restStressDuration: int
    mediumStressDuration: int


class StressEntry(BaseModel):
    calendarDate: str
    values: StressValues


@dataclass
class GarminStressRespone:
    entries: list[StressEntry]

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> "GarminStressRespone":
        adapter = TypeAdapter(list[StressEntry])
        entries = adapter.validate_python(json_dict)
        return cls(entries)
