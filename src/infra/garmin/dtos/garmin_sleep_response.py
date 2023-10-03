from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, TypeAdapter


class Values(BaseModel):
    deepSleepSeconds: int
    awakeSleepSeconds: int
    totalSleepSeconds: int  # Total sleep does not include awake time
    lightSleepSeconds: int
    REMSleepSeconds: int


class SleepEntry(BaseModel):
    calendarDate: date
    values: Values


@dataclass
class GarminSleepResponse:
    entries: list[SleepEntry]

    @staticmethod
    def from_json(json: Any) -> "GarminSleepResponse":
        adapter = TypeAdapter(list[SleepEntry])
        entries = adapter.validate_python(json)
        return GarminSleepResponse(entries)
