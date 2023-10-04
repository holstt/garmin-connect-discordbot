from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.garmin_api_client import JsonResponseType


class RhrValues(BaseModel):
    restingHR: int
    wellnessMaxAvgHR: int
    wellnessMinAvgHR: int


class RhrEntry(BaseModel):
    calendarDate: date
    values: RhrValues


@dataclass
class GarminRhrResponse:
    entries: list[RhrEntry]

    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminRhrResponse":
        adapter = TypeAdapter(list[RhrEntry])
        entries = adapter.validate_python(json)
        return GarminRhrResponse(entries)
