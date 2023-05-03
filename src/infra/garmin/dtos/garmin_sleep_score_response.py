from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, List, Type, TypeVar, cast

import dateutil.parser

T = TypeVar("T")


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]  # type: ignore


@dataclass
class SleepScoreElement:
    calendar_date: datetime
    value: int

    @staticmethod
    def from_dict(obj: Any) -> "SleepScoreElement":
        assert isinstance(obj, dict)
        calendar_date = from_datetime(obj.get("calendarDate"))
        value = from_int(obj.get("value"))
        return SleepScoreElement(calendar_date, value)


@dataclass
class GarminSleepScoreResponse:
    entries: list[SleepScoreElement]

    @staticmethod
    def from_list(s: Any) -> "GarminSleepScoreResponse":
        data = from_list(SleepScoreElement.from_dict, s)
        return GarminSleepScoreResponse(data)
