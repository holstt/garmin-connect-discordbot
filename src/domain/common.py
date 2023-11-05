import datetime
from dataclasses import dataclass
from datetime import timedelta

from src.consts import DAYS_IN_FOUR_WEEKS, DAYS_IN_WEEK, DAYS_IN_YEAR


@dataclass(frozen=True)
class DatePeriod:
    start: datetime.date
    end: datetime.date

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("Start date must be before end date")

    # Returns a list of dates in the period (includes both start and end date)
    def get_date_range(self) -> list[datetime.date]:
        return [
            self.start + timedelta(days=i)
            for i in range((self.end - self.start).days + 1)
        ]

    # Returns the number of days in the period (includes both start and end date)
    def get_num_days(self) -> int:
        return (self.end - self.start).days + 1

    # NB: It seems Garmin only allows fetching periods for: 7 days, 4 weeks, 1 year
    @staticmethod
    def from_last_7_days(end_date: datetime.date) -> "DatePeriod":
        return DatePeriod(end_date - timedelta(days=DAYS_IN_WEEK - 1), end_date)

    @staticmethod
    def from_last_4_weeks(end_date: datetime.date) -> "DatePeriod":
        return DatePeriod(end_date - timedelta(days=DAYS_IN_FOUR_WEEKS - 1), end_date)

    @staticmethod
    def from_last_1_year(end_date: datetime.date) -> "DatePeriod":
        return DatePeriod(end_date - timedelta(days=DAYS_IN_YEAR - 1), end_date)
