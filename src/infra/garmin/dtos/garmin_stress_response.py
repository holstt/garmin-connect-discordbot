# from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType

T = TypeVar("T")


# If no duration in stress segment, value will be none
# Values are in seconds
class StressValues(BaseModel):
    highStressDuration: Optional[int]
    lowStressDuration: Optional[int]
    overallStressLevel: int
    restStressDuration: Optional[int]
    mediumStressDuration: Optional[int]


class StressEntry(BaseModel, GarminResponseEntryDto):
    values: StressValues


@dataclass
class GarminStressResponse(GarminResponseDto[StressEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminStressResponse":
        entries = GarminStressResponse._from_json_list(json, StressEntry)
        return GarminStressResponse(entries)
