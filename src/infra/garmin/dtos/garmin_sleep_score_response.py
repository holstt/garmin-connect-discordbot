import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.garmin_api_client import JsonResponseType


class SleepScoreEntry(BaseModel):
    calendarDate: date
    value: int


@dataclass
class GarminSleepScoreResponse:
    entries: list[SleepScoreEntry]

    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminSleepScoreResponse":
        adapter = TypeAdapter(list[SleepScoreEntry])
        entries = adapter.validate_python(json)
        return GarminSleepScoreResponse(entries)
