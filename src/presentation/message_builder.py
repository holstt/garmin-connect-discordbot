from datetime import timedelta
from typing import Optional

from src.domain.metrics import HrvMetrics, SimpleMetric, SleepMetrics
from src.infra.garmin.dtos.garmin_response import GarminResponseEntryDto
from src.presentation.view_models import DiffToTarget, MetricViewModel


# Generic builder for SimpleMetric subtypes
def metric_message(
    name: str,
    icon: str,
    metric: SimpleMetric[GarminResponseEntryDto],
    with_max_val: Optional[int] = None,
) -> MetricViewModel:
    recent_str = str(metric.latest)
    week_avg_str = str(round(metric.weekly_avg))
    diff_to_avg_str = _value_to_signed_str(round(metric.diff_to_weekly_avg))
    out_of_max_str = f"/{with_max_val}" if with_max_val is not None else ""

    return MetricViewModel(
        name=name,
        icon=icon,
        recent=recent_str,
        diff_to_avg=diff_to_avg_str,
        diff_to_avg_emoji=_get_diff_emoji(
            metric.is_higher_better, round(metric.diff_to_weekly_avg)
        ),
        week_avg=week_avg_str,
        out_of_max=out_of_max_str,
    )


# Specific builder for HRV
def hrv_message(name: str, icon: str, hrv_metrics: HrvMetrics) -> MetricViewModel:
    hrv_recent_str = str(hrv_metrics.latest)
    week_avg_str = str(hrv_metrics.weekly_avg)
    diff_to_avg_str = (
        _value_to_signed_str(hrv_metrics.diff_to_weekly_avg)
        if hrv_metrics.diff_to_weekly_avg is not None
        else "N/A"
    )

    diff_to_avg_emoji = (
        _get_diff_emoji(
            hrv_metrics.is_higher_better, round(hrv_metrics.diff_to_weekly_avg)
        )
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


# Specific builder for Sleep
def sleep_message(name: str, icon: str, sleep_metrics: SleepMetrics) -> MetricViewModel:
    recent_str = _format_timedelta(sleep_metrics.latest)
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
            round(sleep_metrics.diff_to_weekly_avg.total_seconds()),
        ),
        week_avg=week_avg_str,
        out_of_max="",
        diff_to_target=DiffToTarget(target_name="8h", diff=diff_to_8h_str),
    )


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


def _get_diff_emoji(is_positive_best: bool, diff: float) -> str:
    if diff > 0 and is_positive_best or diff < 0 and not is_positive_best:
        return "🟢"
    elif diff is 0:
        return "⚪"
    else:
        return "🔴"
