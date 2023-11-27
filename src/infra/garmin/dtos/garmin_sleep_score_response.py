import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter, validator

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class SleepScoreEntry(BaseModel, GarminResponseEntryDto):
    value: int

    # Set value to 0 if None provided. Value is none if Garmin was not able to calculate sleep score for that day (rare case)
    @validator("value", pre=True, always=True)
    def set_none_to_zero(cls, v: int | None) -> int:
        return v if v is not None else 0


@dataclass
class GarminSleepScoreResponse(GarminResponseDto[SleepScoreEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminSleepScoreResponse":
        list = GarminSleepScoreResponse._from_json_list(json, SleepScoreEntry)
        return GarminSleepScoreResponse(list)
