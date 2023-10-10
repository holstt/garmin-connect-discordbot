from datetime import date
from io import BytesIO
from typing import NamedTuple, Optional


class DiffToTarget(NamedTuple):
    target_name: str
    diff: str


class MetricPlot(NamedTuple):
    id: str
    data: BytesIO


class HealthSummaryViewModel(NamedTuple):
    date: date
    metrics: list["MetricViewModel"]
    # plots: list[MetricPlot]


class MetricViewModel(NamedTuple):
    name: str
    icon: str
    recent: str
    diff_to_avg: str
    diff_to_avg_emoji: str
    week_avg: str
    out_of_max: str
    diff_to_target: Optional[DiffToTarget] = None

    # XXX: Decouple -> Use different strategies for each message format?
    # TODO: Move to MessageStrategy
    def to_line(self) -> str:
        diff_to_target_str = (
            f", Δ {self.diff_to_target.target_name}: {self.diff_to_target.diff}"
            if self.diff_to_target
            else ""
        )
        return f"```{self.icon} {self.name}: {self.recent}{self.out_of_max} - (weekly avg: {self.week_avg}{self.out_of_max}, Δ avg: {self.diff_to_avg}{diff_to_target_str})```"

    def to_table_row(self) -> list[str]:
        return [
            self.icon,
            f"{self.recent}{self.out_of_max}",
            f"{self.diff_to_avg} {self.diff_to_avg_emoji}",
            f"{self.week_avg}{self.out_of_max}",
            self.name,
            f"{self.diff_to_target.target_name}: {self.diff_to_target.diff}"
            if self.diff_to_target
            else "",
        ]
