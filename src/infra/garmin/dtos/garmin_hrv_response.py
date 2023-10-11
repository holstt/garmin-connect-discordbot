from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

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


# Make both private and public class, such that public class has same structure as other dto responses
class _GarminHrvResponseInternal(BaseModel):
    hrvSummaries: Sequence[HrvSummary]
    userProfilePk: int


@dataclass
class GarminHrvResponse(GarminResponseDto[HrvSummary]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminHrvResponse":
        internal_class = GarminHrvResponse._from_json_obj(
            json, _GarminHrvResponseInternal
        )
        return GarminHrvResponse(internal_class.hrvSummaries)
