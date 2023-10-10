from dataclasses import dataclass
from datetime import date
from typing import Any, Sequence

from pydantic import BaseModel, Field, TypeAdapter

from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)
from src.infra.garmin.garmin_api_client import JsonResponseType


class BodyBatteryValueDescriptorDTOListItem(BaseModel):
    bodyBatteryValueDescriptorIndex: int
    bodyBatteryValueDescriptorKey: str


class BbEntry(BaseModel, GarminResponseEntryDto):
    calendarDate: date = Field(
        alias="date"
    )  # use alias to follow naming of other DTOs...
    charged: int
    drained: int
    # Time range bb data recorded for
    startTimestampGMT: str
    endTimestampGMT: str
    startTimestampLocal: str
    endTimestampLocal: str  # If today, will be time of last sync with watch
    # Each entry in list is a list of 2 ints: [timestamp, value]. To find max bb for the day, find the max value in the list
    bodyBatteryValuesArray: Sequence[Sequence[int]]
    bodyBatteryValueDescriptorDTOList: Sequence[BodyBatteryValueDescriptorDTOListItem]


@dataclass
class GarminBbResponse(GarminResponseDto[BbEntry]):
    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminBbResponse":
        entries = GarminBbResponse._from_json_list(json, BbEntry)
        return GarminBbResponse(entries)
