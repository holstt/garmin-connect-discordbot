from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.garmin_api_client import JsonResponseType


class StepsEntry(BaseModel):
    calendarDate: date
    totalSteps: int
    totalDistance: int
    stepGoal: int


@dataclass
class GarminStepsResponse:
    entries: list[StepsEntry]

    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminStepsResponse":
        adapter = TypeAdapter(list[StepsEntry])
        entries = adapter.validate_python(json)
        return GarminStepsResponse(entries)
