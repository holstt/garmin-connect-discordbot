import datetime
import stat
from dataclasses import dataclass
from datetime import timedelta

from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse

# NB! There may be gaps in data if metric not registered for some reason (e.g. if not always wearing device during sleep)


@dataclass(frozen=True)
class DatePeriod:
    start: datetime.date
    end: datetime.date

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("Start date must be before end date")

    # NB: It seems Garmin only allows fetching periods for: 7 days, 4 weeks, 1 year
    @staticmethod
    def from_last_7_days(date: datetime.date) -> "DatePeriod":
        return DatePeriod(date - timedelta(days=6), date)

    @staticmethod
    def from_last_4_weeks(date: datetime.date) -> "DatePeriod":
        return DatePeriod(date - timedelta(days=27), date)


class SleepScoreMetrics:
    def __init__(self, sleep_data: GarminSleepScoreResponse):
        self._entries = sorted(sleep_data.entries, key=lambda x: x.calendarDate)

    @property
    # Get the most recent entry
    def current(self) -> int:
        return self._entries[-1].value

    @property
    # Returns average for the period
    def avg(self) -> float:
        total = sum([entry.value for entry in self._entries])
        avg = total / len(self._entries)
        return avg

    @property
    def diff_to_average(self) -> float:
        return self.current - self.avg

    def get_diff_to_target(self, target: int) -> int:
        return self.current - target


class SleepMetrics:  # XXX: // SleepSummary
    def __init__(self, sleep_data: GarminSleepResponse):
        # Ensure sorted by date such that the most recent entry is last
        self._entries = sorted(sleep_data.entries, key=lambda x: x.calendarDate)

    @property
    def entries(self):
        return self._entries

    @property
    # Returns average sleep time for the sleep data period
    def avg(self) -> timedelta:
        total_sleep_seconds = sum([x.values.totalSleepSeconds for x in self._entries])
        average_sleep_seconds = total_sleep_seconds / len(self._entries)
        average_sleep = timedelta(seconds=average_sleep_seconds)
        return average_sleep

    @property
    # Get the most recent sleep entry
    def current(self) -> timedelta:
        return timedelta(seconds=self._entries[-1].values.totalSleepSeconds)

    @property
    def diff_to_average(self) -> timedelta:
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
    # Returns none if no hrv registered for the night
    def diff_to_average(self) -> int | None:
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
