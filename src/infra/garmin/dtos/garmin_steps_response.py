from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, TypeAdapter


class StepsEntry(BaseModel):
    calendarDate: str
    totalSteps: int
    totalDistance: int
    stepGoal: int


@dataclass
class GarminStepsResponse:
    entries: list[StepsEntry]

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> "GarminStepsResponse":
        adapter = TypeAdapter(list[StepsEntry])
        entries = adapter.validate_python(json_dict)
        return cls(entries)
