from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, TypeAdapter


class SleepScoreEntry(BaseModel):
    calendarDate: date
    value: int


@dataclass
class GarminSleepScoreResponse:
    entries: list[SleepScoreEntry]

    @staticmethod
    def from_json(json: Any) -> "GarminSleepScoreResponse":
        adapter = TypeAdapter(list[SleepScoreEntry])
        entries = adapter.validate_python(json)
        return GarminSleepScoreResponse(entries)
