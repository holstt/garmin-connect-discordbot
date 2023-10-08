from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class RhrValues(BaseModel):
    restingHR: int
    wellnessMaxAvgHR: int
    wellnessMinAvgHR: int


class RhrEntry(BaseModel, GarminResponseEntryDto):
    calendarDate: date
    values: RhrValues


@dataclass
class GarminRhrResponse(GarminResponseDto[RhrEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminRhrResponse":
        entries = GarminRhrResponse._from_json_list(json, RhrEntry)
        return GarminRhrResponse(entries)
