from datetime import timedelta
from typing import NamedTuple, Optional

from src.domain.metrics import HrvMetrics, SimpleMetric, SleepMetrics


class DiffToTarget(NamedTuple):
    target_name: str
    diff: str


class MetricViewModel(NamedTuple):
    name: str
    icon: str
    recent: str
    diff_to_avg: str
    diff_to_avg_emoji: str
    week_avg: str
    out_of_max: str
    diff_to_target: Optional[DiffToTarget] = None

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


def _value_to_signed_str(value: float) -> str:
    return f"{_get_sign(value)}{abs(value)}"


# Returns sign of value
def _get_sign(value: float) -> str:
    return "-" if value < 0 else "+" if value > 0 else ""


def _format_timedelta(delta: timedelta, should_include_sign: bool = False) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remaining_seconds = divmod(abs(total_seconds), 3600)
    minutes = remaining_seconds // 60
    # Get sign
    sign = _get_sign(total_seconds) if should_include_sign else ""
    if hours == 0:
        return f"{sign}{minutes}m"
    return f"{sign}{hours}h{minutes}m"


# Generic helper for simple metrics
def metric(
    name: str, icon: str, metric: SimpleMetric, with_max_val: Optional[int] = None
):
    recent_str = str(metric.current)
    week_avg_str = str(round(metric.weekly_avg))
    diff_to_avg_str = _value_to_signed_str(round(metric.diff_to_weekly_avg))
    out_of_max_str = f"/{with_max_val}" if with_max_val is not None else ""

    return MetricViewModel(
        name=name,
        icon=icon,
        recent=recent_str,
        diff_to_avg=diff_to_avg_str,
        diff_to_avg_emoji=_get_diff_emoji(
            metric.is_higher_better, metric.diff_to_weekly_avg
        ),
        week_avg=week_avg_str,
        out_of_max=out_of_max_str,
    )


def _get_diff_emoji(is_positive_best: bool, diff: float) -> str:
    if diff > 0 and is_positive_best or diff < 0 and not is_positive_best:
        return "🟢"
    else:
        return "🔴"


def hrv(name: str, icon: str, hrv_metrics: HrvMetrics):
    hrv_recent_str = str(hrv_metrics.current)
    week_avg_str = str(hrv_metrics.weekly_avg)
    diff_to_avg_str = (
        _value_to_signed_str(hrv_metrics.diff_to_weekly_avg)
        if hrv_metrics.diff_to_weekly_avg is not None
        else "N/A"
    )

    diff_to_avg_emoji = (
        _get_diff_emoji(hrv_metrics.is_higher_better, hrv_metrics.diff_to_weekly_avg)
        if hrv_metrics.diff_to_weekly_avg is not None
        else ""
    )

    return MetricViewModel(
        name=name,
        icon=icon,
        recent=hrv_recent_str,
        diff_to_avg=diff_to_avg_str,
        diff_to_avg_emoji=diff_to_avg_emoji,
        week_avg=week_avg_str,
        out_of_max="",
    )


def sleep(name: str, icon: str, sleep_metrics: SleepMetrics):
    recent_str = _format_timedelta(sleep_metrics.current)
    week_avg_str = _format_timedelta(sleep_metrics.weekly_avg)
    diff_to_avg_str = _format_timedelta(
        sleep_metrics.diff_to_weekly_avg, should_include_sign=True
    )
    diff_to_8h_str = _format_timedelta(
        sleep_metrics.get_diff_to_hour(8), should_include_sign=True
    )

    return MetricViewModel(
        name=name,
        icon=icon,
        recent=recent_str,
        diff_to_avg=diff_to_avg_str,
        diff_to_avg_emoji=_get_diff_emoji(
            sleep_metrics.is_higher_better,
            sleep_metrics.diff_to_weekly_avg.total_seconds(),
        ),
        week_avg=week_avg_str,
        out_of_max="",
        diff_to_target=DiffToTarget(target_name="8h", diff=diff_to_8h_str),
    )
