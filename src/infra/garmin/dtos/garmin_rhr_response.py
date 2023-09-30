import json
from dataclasses import dataclass
from typing import Any, TypeVar

from pydantic import BaseModel, TypeAdapter


class RhrValues(BaseModel):
    restingHR: int
    wellnessMaxAvgHR: int
    wellnessMinAvgHR: int


class RhrEntry(BaseModel):
    calendarDate: str
    values: RhrValues


@dataclass
class GarminRhrResponse:
    entries: list[RhrEntry]

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> "GarminRhrResponse":
        adapter = TypeAdapter(list[RhrEntry])
        entries = adapter.validate_python(json_dict)
        return cls(entries)
