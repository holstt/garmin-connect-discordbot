import random
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class SleepScoreEntry(BaseModel, GarminResponseEntryDto):
    value: int


@dataclass
class GarminSleepScoreResponse(GarminResponseDto[SleepScoreEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminSleepScoreResponse":
        list = GarminSleepScoreResponse._from_json_list(json, SleepScoreEntry)
        return GarminSleepScoreResponse(list)
