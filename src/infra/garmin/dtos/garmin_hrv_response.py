from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, TypeAdapter

from src.infra.garmin.garmin_api_client import JsonResponseType


class Baseline(BaseModel):
    lowUpper: int
    balancedLow: int
    balancedUpper: int
    markerValue: float


class HrvSummary(BaseModel):
    calendarDate: date
    weeklyAvg: int
    lastNightAvg: Optional[int]
    lastNight5MinHigh: Optional[int]
    baseline: Baseline
    status: str
    feedbackPhrase: str
    createTimeStamp: datetime


class GarminHrvResponse(BaseModel):
    # hrvSummaries: list[HrvSummary]
    entries: list[HrvSummary] = Field(..., alias="hrvSummaries")
    userProfilePk: int

    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminHrvResponse":
        adapter = TypeAdapter(GarminHrvResponse)
        obj = adapter.validate_python(json)
        return obj
