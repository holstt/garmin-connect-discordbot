import datetime
from abc import ABC
from dataclasses import dataclass
from datetime import timedelta
from io import BytesIO
from typing import Callable, TypeVar

from src.infra.garmin.dtos.garmin_bb_response import GarminBbResponse
from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_rhr_response import GarminRhrResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.garmin.dtos.garmin_stress_response import GarminStressResponse

T = TypeVar("T")


def average_by(items: list[T], prop_selector: Callable[[T], float]) -> float:
    total = sum(prop_selector(item) for item in items)
    return total / len(items) if items else 0.0


from typing import Callable, TypeVar

P = TypeVar("P")


class SimpleMetric(ABC):
    def __init__(self, entries: list[P], selector: Callable[[P], float]):
        self._entries = entries
        self.selector = selector

    @property
    def entries(self):
        return self._entries

    # Get the most recent entry
    @property
    def current(self) -> float:
        return self.selector(self.entries[-1])

    # Return average for the period
    @property
    def avg(self) -> float:
        return average_by(self.entries, self.selector)

    @property
    def weekly_avg(self) -> float:
        return average_by(self.entries[-7:], self.selector)

    @property
    def diff_to_avg(self) -> float:
        return self.current - self.avg

    @property
    def diff_to_weekly_avg(self) -> float:
        return self.current - self.weekly_avg

    def diff_to_target(self, target: float) -> float:
        return self.current - target


# NB! There may be gaps in data if metric not registered for some reason (e.g. if not always wearing device during sleep)


class RhrMetrics(SimpleMetric):
    def __init__(self, rhr_data: GarminRhrResponse):
        entries = sorted(rhr_data.entries, key=lambda x: x.calendarDate)
        super().__init__(entries, lambda x: x.values.restingHR)


class BodyBatteryMetrics(SimpleMetric):
    def __init__(self, bb_data: GarminBbResponse):
        entries = sorted(bb_data.entries, key=lambda x: x.calendarDate)
        super().__init__(
            entries, lambda x: max(val for (time, val) in x.bodyBatteryValuesArray)
        )


class StressMetrics(SimpleMetric):
    def __init__(self, stress_data: GarminStressResponse):
        entries = sorted(stress_data.entries, key=lambda x: x.calendarDate)
        super().__init__(entries, lambda x: x.values.overallStressLevel)


class SleepScoreMetrics(SimpleMetric):
    def __init__(self, sleep_data: GarminSleepScoreResponse):
        entries = sorted(sleep_data.entries, key=lambda x: x.calendarDate)
        super().__init__(entries, lambda x: x.value)


class SleepMetrics:  # XXX: // SleepSummary
    def __init__(self, sleep_data: GarminSleepResponse):
        # Ensure sorted by date such that the most recent entry is last
        self._entries = sorted(sleep_data.entries, key=lambda x: x.calendarDate)

    @property
    def entries(self):
        return self._entries

    @property
    # Get the most recent sleep entry
    def current(self) -> timedelta:
        return timedelta(seconds=self._entries[-1].values.totalSleepSeconds)

    @property
    # Returns average sleep time for the sleep data period
    def avg(self) -> timedelta:
        average_sleep_seconds = average_by(
            self._entries, lambda x: x.values.totalSleepSeconds
        )
        return timedelta(seconds=average_sleep_seconds)

    @property
    def weekly_avg(self) -> timedelta:
        average_sleep_seconds = average_by(
            self._entries[-7:], lambda x: x.values.totalSleepSeconds
        )
        return timedelta(seconds=average_sleep_seconds)

    @property
    def diff_to_weekly_avg(self) -> timedelta:
        return self.current - self.weekly_avg

    @property
    def diff_to_avg(self) -> timedelta:
        return self.current - self.avg

    def get_diff_to_hour(self, hour: int) -> timedelta:
        return self.current - timedelta(hours=hour)


class HrvMetrics:
    def __init__(self, hrv_data: GarminHrvResponse) -> None:
        self._entries = sorted(hrv_data.entries, key=lambda x: x.calendarDate)

    @property
    # Returns none if no hrv registered for the night
    def current(self) -> int | None:
        return self._entries[-1].lastNightAvg

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
        return self.current - self.weekly_avg if self.current else None

    @property
    # Get wether hrv is balanced or not
    def is_hrv_balanced(self) -> bool:
        return self._entries[-1].status == "BALANCED"


@dataclass(frozen=True)
class HealthSummary:
    date: datetime.date
    sleep: SleepMetrics
    hrv: HrvMetrics
    sleep_score: SleepScoreMetrics
    rhr: RhrMetrics
    bb: BodyBatteryMetrics
    stress: StressMetrics
    sleep_plot: BytesIO
    metrics_plot: BytesIO