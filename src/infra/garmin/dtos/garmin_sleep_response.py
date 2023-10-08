import stat
from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class Values(BaseModel):
    deepSleepSeconds: int
    awakeSleepSeconds: int
    totalSleepSeconds: int  # Total sleep does not include awake time
    lightSleepSeconds: int
    REMSleepSeconds: int


class SleepEntry(BaseModel, GarminResponseEntryDto):
    values: Values


@dataclass
class GarminSleepResponse(GarminResponseDto[SleepEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminSleepResponse":
        entries = GarminSleepResponse._from_json_list(json, SleepEntry)
        return GarminSleepResponse(entries)
