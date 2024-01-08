import datetime
from abc import ABC
from copy import copy
from dataclasses import dataclass
from datetime import timedelta

from typing import Any, Callable, Generic, Optional, Sequence, TypeVar

from src.consts import DAYS_IN_WEEK
from src.infra.garmin.dtos import *

L = TypeVar("L", covariant=True)  # List type
R = TypeVar("R")  # Return type


def average_by(items: Sequence[L], prop_selector: Callable[[L], float]) -> float:
    total = sum(prop_selector(item) for item in items)
    return total / len(items) if items else 0.0


class BaseMetric(ABC, Generic[L, R]):
    def __init__(
        self,
        entries: Sequence[L],
        selector: Callable[[L], R],
        is_higher_better: bool = True,
    ):
        super().__init__()

        self._entries = entries
        self._selector = selector
        self.is_higher_better = is_higher_better

    # Make a shallow copy with reduced entries
    def with_last_n(self, n: int):
        instance_copy = copy(self)
        instance_copy._entries = self._entries[-n:]
        return instance_copy

    @property
    def entries(self):
        return self._entries
        # return [self._selector(entry) for entry in self._entries]

    @property
    def latest(self) -> R:
        return self._selector(self.entries[-1])
        # return self.entries[-1]


class SimpleMetric(BaseMetric[L, float], ABC):
    def __init__(
        self,
        entries: Sequence[L],
        selector: Callable[[L], float],
        is_higher_better: bool = True,
    ):
        super().__init__(entries, selector, is_higher_better)

    # Return average for the period
    @property
    def avg(self) -> float:
        return average_by(self.entries, self._selector)

    @property
    def weekly_avg(self) -> float:
        return average_by(self.entries[-DAYS_IN_WEEK:], self._selector)

    @property
    def diff_to_avg(self) -> float:
        return self.latest - self.avg

    @property
    def diff_to_weekly_avg(self) -> float:
        return self.latest - self.weekly_avg

    def diff_to_target(self, target: float) -> float:
        return self.latest - target


# NB! There may be gaps in data if metric not registered for some reason (e.g. if not always wearing device during sleep)


class RhrMetrics(SimpleMetric[RhrEntry]):
    def __init__(self, rhr_data: GarminRhrResponse):
        entries = sorted(rhr_data.entries, key=lambda x: x.calendarDate)
        super().__init__(entries, lambda x: x.values.restingHR, is_higher_better=False)


class BbMetrics(SimpleMetric[BbEntry]):
    def __init__(self, bb_data: GarminBbResponse):
        entries = sorted(bb_data.entries, key=lambda x: x.calendarDate)
        super().__init__(
            entries, lambda x: max(val for (time, val) in x.bodyBatteryValuesArray)
        )


class StressMetrics(SimpleMetric[StressEntry]):
    def __init__(self, stress_data: GarminStressResponse):
        entries = sorted(stress_data.entries, key=lambda x: x.calendarDate)
        super().__init__(
            entries, lambda x: x.values.overallStressLevel, is_higher_better=False
        )


class SleepScoreMetrics(SimpleMetric[SleepScoreEntry]):
    def __init__(self, sleep_data: GarminSleepScoreResponse):
        entries = sorted(sleep_data.entries, key=lambda x: x.calendarDate)
        super().__init__(entries, lambda x: x.value)


class SleepMetrics(BaseMetric[SleepEntry, timedelta]):  # XXX: // SleepSummary
    def __init__(self, sleep_data: GarminSleepResponse):
        # Ensure sorted by date such that the most recent entry is last
        entries = sorted(sleep_data.entries, key=lambda x: x.calendarDate)
        super().__init__(
            entries, lambda x: timedelta(seconds=x.values.totalSleepSeconds)
        )

    @property
    # Returns average sleep time for the sleep data period
    def avg(self) -> timedelta:
        average_sleep_seconds = average_by(
            self.entries, lambda x: x.values.totalSleepSeconds
        )
        return timedelta(seconds=average_sleep_seconds)

    # XXX: Remove this prop?
    @property
    def total(self) -> timedelta:
        return timedelta(
            seconds=(sum(entry.values.totalSleepSeconds for entry in self.entries))
        )

    @property
    def weekly_avg(self) -> timedelta:
        average_sleep_seconds = average_by(
            self._entries[-DAYS_IN_WEEK:], lambda x: x.values.totalSleepSeconds
        )
        return timedelta(seconds=average_sleep_seconds)

    @property
    def diff_to_weekly_avg(self) -> timedelta:
        return self.latest - self.weekly_avg

    @property
    def diff_to_avg(self) -> timedelta:
        return self.latest - self.avg

    def get_diff_to_hour(self, hour: int) -> timedelta:
        return self.latest - timedelta(hours=hour)


class HrvMetrics(BaseMetric[HrvSummary, Optional[int]]):
    def __init__(self, hrv_data: GarminHrvResponse) -> None:
        self._entries = sorted(hrv_data.entries, key=lambda x: x.calendarDate)
        super().__init__(
            self._entries,
            lambda x: x.lastNightAvg if x.lastNightAvg else None,
        )

    @property
    # Get the most recent registered weekly hrv average
    def weekly_avg(self) -> int:
        return self._entries[-1].weeklyAvg

    @property
    def avg(self) -> float:
        return average_by(
            self._entries, lambda x: x.lastNightAvg if x.lastNightAvg else 0
        )

    @property
    # Returns none if no hrv registered for the night
    def diff_to_weekly_avg(self) -> int | None:
        return self.latest - self.weekly_avg if self.latest else None

    @property
    # Get wether hrv is balanced or not
    def is_hrv_balanced(self) -> bool:
        return self._entries[-1].status == "BALANCED"


# Represents data for a health summary
@dataclass(frozen=True)
class HealthSummary:
    date: datetime.date
    # plots: Sequence[MetricPlot]
    metrics: Sequence[BaseMetric[GarminResponseEntryDto, Any]]
