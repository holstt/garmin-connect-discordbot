from dataclasses import dataclass
from datetime import date
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter

from src.infra.garmin.garmin_api_client import JsonResponseType


class BodyBatteryValueDescriptorDTOListItem(BaseModel):
    bodyBatteryValueDescriptorIndex: int
    bodyBatteryValueDescriptorKey: str


class BbEntry(BaseModel):
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
    bodyBatteryValuesArray: list[list[int]]
    bodyBatteryValueDescriptorDTOList: list[BodyBatteryValueDescriptorDTOListItem]


@dataclass
class GarminBbResponse:
    entries: list[BbEntry]

    @staticmethod
    def from_json(json: JsonResponseType) -> "GarminBbResponse":
        adapter = TypeAdapter(list[BbEntry])
        entries = adapter.validate_python(json)
        return GarminBbResponse(entries)
