from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, List, Optional, Type, TypeVar, cast

import dateutil.parser

T = TypeVar("T")


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_float(x: Any) -> float:
    assert isinstance(x, (float, int)) and not isinstance(x, bool)
    return float(x)


def to_float(x: Any) -> float:
    assert isinstance(x, float)
    return x


def from_datetime(x: Any) -> datetime:
    return dateutil.parser.parse(x)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs: list[Any], x: Any):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:  # type: ignore
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]  # type: ignore


@dataclass
class Baseline:
    low_upper: int
    balanced_low: int
    balanced_upper: int
    marker_value: float

    @staticmethod
    def from_dict(obj: Any) -> "Baseline":
        assert isinstance(obj, dict)
        low_upper = from_int(obj.get("lowUpper"))
        balanced_low = from_int(obj.get("balancedLow"))
        balanced_upper = from_int(obj.get("balancedUpper"))
        marker_value = from_float(obj.get("markerValue"))
        return Baseline(low_upper, balanced_low, balanced_upper, marker_value)


@dataclass
class HrvSummary:
    calendar_date: datetime
    weekly_avg: int
    baseline: Baseline
    status: str
    feedback_phrase: str
    create_time_stamp: datetime
    last_night_avg: Optional[int] = None
    last_night5_min_high: Optional[int] = None

    @staticmethod
    def from_dict(obj: Any) -> "HrvSummary":
        assert isinstance(obj, dict)
        calendar_date = from_datetime(obj.get("calendarDate"))
        weekly_avg = from_int(obj.get("weeklyAvg"))
        baseline = Baseline.from_dict(obj.get("baseline"))
        status = from_str(obj.get("status"))
        feedback_phrase = from_str(obj.get("feedbackPhrase"))
        create_time_stamp = from_datetime(obj.get("createTimeStamp"))
        last_night_avg = from_union([from_int, from_none], obj.get("lastNightAvg"))
        last_night5_min_high = from_union(
            [from_int, from_none], obj.get("lastNight5MinHigh")
        )
        return HrvSummary(
            calendar_date,
            weekly_avg,
            baseline,
            status,
            feedback_phrase,
            create_time_stamp,
            last_night_avg,
            last_night5_min_high,
        )


@dataclass
class GarminHrvResponse:
    hrv_summaries: List[HrvSummary]
    user_profile_pk: int

    @staticmethod
    def from_dict(obj: Any) -> "GarminHrvResponse":
        assert isinstance(obj, dict)
        hrv_summaries = from_list(HrvSummary.from_dict, obj.get("hrvSummaries"))
        user_profile_pk = from_int(obj.get("userProfilePk"))
        return GarminHrvResponse(hrv_summaries, user_profile_pk)
