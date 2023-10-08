from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class Baseline(BaseModel):
    lowUpper: int
    balancedLow: int
    balancedUpper: int
    markerValue: float


class HrvSummary(BaseModel, GarminResponseEntryDto):
    weeklyAvg: int
    lastNightAvg: Optional[int]
    lastNight5MinHigh: Optional[int]
    baseline: Baseline
    status: str
    feedbackPhrase: str
    createTimeStamp: datetime


class GarminHrvResponse(BaseModel, GarminResponseDto[HrvSummary]):
    entries: list[HrvSummary] = Field(..., alias="hrvSummaries")
    userProfilePk: int

    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminHrvResponse":
        return GarminHrvResponse._from_json_obj(json, GarminHrvResponse)
