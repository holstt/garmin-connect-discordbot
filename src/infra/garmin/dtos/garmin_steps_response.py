from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, TypeAdapter


class StepsEntry(BaseModel):
    calendarDate: date
    totalSteps: int
    totalDistance: int
    stepGoal: int


@dataclass
class GarminStepsResponse:
    entries: list[StepsEntry]

    @staticmethod
    def from_json(json: Any) -> "GarminStepsResponse":
        adapter = TypeAdapter(list[StepsEntry])
        entries = adapter.validate_python(json)
        return GarminStepsResponse(entries)
