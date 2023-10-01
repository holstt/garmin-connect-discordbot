from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, TypeAdapter


# If no duration in stress segment, value will be none
class StressValues(BaseModel):
    highStressDuration: Optional[int]
    lowStressDuration: Optional[int]
    overallStressLevel: int
    restStressDuration: Optional[int]
    mediumStressDuration: Optional[int]


class StressEntry(BaseModel):
    calendarDate: str
    values: StressValues


@dataclass
class GarminStressRespone:
    entries: list[StressEntry]

    @staticmethod
    def from_json(json_dict: dict[str, Any]) -> "GarminStressRespone":
        adapter = TypeAdapter(list[StressEntry])
        entries = adapter.validate_python(json_dict)
        return GarminStressRespone(entries)
