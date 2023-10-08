from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, TypeAdapter

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class StepsEntry(BaseModel, GarminResponseEntryDto):
    totalSteps: int
    totalDistance: int
    stepGoal: int


@dataclass
class GarminStepsResponse(GarminResponseDto[StepsEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminStepsResponse":
        list = GarminStepsResponse._from_json_list(json, StepsEntry)
        return GarminStepsResponse(list)
