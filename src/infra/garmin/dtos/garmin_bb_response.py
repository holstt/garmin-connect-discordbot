from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, TypeAdapter


class BodyBatteryValueDescriptorDTOListItem(BaseModel):
    bodyBatteryValueDescriptorIndex: int
    bodyBatteryValueDescriptorKey: str


class BbEntry(BaseModel):
    date: str
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

    @classmethod
    def from_dict(cls, json_dict: dict[str, Any]) -> "GarminBbResponse":
        adapter = TypeAdapter(list[BbEntry])
        entries = adapter.validate_python(json_dict)
        return cls(entries)
