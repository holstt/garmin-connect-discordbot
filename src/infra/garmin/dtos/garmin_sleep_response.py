from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, List, TypeVar

import dateutil.parser

T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]  # type: ignore


@dataclass
class Values:
    deep_sleep_seconds: int
    awake_sleep_seconds: int
    total_sleep_seconds: int
    light_sleep_seconds: int
    rem_sleep_seconds: int

    @staticmethod
    def from_dict(obj: Any) -> "Values":
        assert isinstance(obj, dict)
        deep_sleep_seconds = from_int(obj.get("deepSleepSeconds"))
        awake_sleep_seconds = from_int(obj.get("awakeSleepSeconds"))
        total_sleep_seconds = from_int(obj.get("totalSleepSeconds"))
        light_sleep_seconds = from_int(obj.get("lightSleepSeconds"))
        rem_sleep_seconds = from_int(obj.get("REMSleepSeconds"))
        return Values(
            deep_sleep_seconds,
            awake_sleep_seconds,
            total_sleep_seconds,
            light_sleep_seconds,
            rem_sleep_seconds,
        )


@dataclass
class SleepEntry:
    calendar_date: datetime
    values: Values

    @staticmethod
    def from_dict(obj: Any) -> "SleepEntry":
        assert isinstance(obj, dict)
        calendar_date = from_datetime(obj.get("calendarDate"))
        values = Values.from_dict(obj.get("values"))
        return SleepEntry(calendar_date, values)


@dataclass
class GarminSleepResponse:
    entries: list[SleepEntry]

    @staticmethod
    def from_list(obj: Any) -> "GarminSleepResponse":
        assert isinstance(obj, list)
        sleep_data = from_list(SleepEntry.from_dict, obj)
        return GarminSleepResponse(sleep_data)
