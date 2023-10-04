import datetime
from dataclasses import dataclass
from datetime import timedelta


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

    @staticmethod
    def from_last_1_year(date: datetime.date) -> "DatePeriod":
        return DatePeriod(date - timedelta(days=364), date)
