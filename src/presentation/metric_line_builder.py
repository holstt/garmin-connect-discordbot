from datetime import timedelta
from typing import Optional

from src.domain.metrics import HrvMetrics, SimpleMetric, SleepMetrics


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
def metric_line(
    name: str, icon: str, metric: SimpleMetric, with_max_val: Optional[int] = None
) -> str:
    recent_str = metric.current
    week_avg_str = round(metric.avg)
    diff_to_avg_str = _value_to_signed_str(round(metric.diff_to_avg))
    out_of_max_str = f"/{with_max_val}" if with_max_val is not None else ""

    return f"```{icon} {name}: {recent_str}{out_of_max_str} - (weekly avg: {week_avg_str}, Δ avg: {diff_to_avg_str})```"


def hrv_line(name: str, icon: str, hrv_metrics: HrvMetrics) -> str:
    hrv_recent_str = hrv_metrics.current
    week_avg_str = hrv_metrics.weekly_avg
    diff_to_avg_str = (
        _value_to_signed_str(hrv_metrics.diff_to_weekly_avg)
        if hrv_metrics.diff_to_weekly_avg is not None
        else "N/A"
    )

    return f"```{icon} {name}: {hrv_recent_str} - (weekly avg: {week_avg_str}, Δ avg: {diff_to_avg_str})```"


def sleep_line(name: str, icon: str, sleep_metrics: SleepMetrics) -> str:
    recent_str = _format_timedelta(sleep_metrics.current)
    week_avg_str = _format_timedelta(sleep_metrics.avg)
    diff_to_avg_str = _format_timedelta(
        sleep_metrics.diff_to_avg, should_include_sign=True
    )
    diff_to_8h_str = _format_timedelta(
        sleep_metrics.get_diff_to_hour(8), should_include_sign=True
    )

    return f"```{icon} {name}: {recent_str} - (weekly avg: {week_avg_str}, Δ avg: {diff_to_avg_str}), Δ 8h: {diff_to_8h_str})```"
