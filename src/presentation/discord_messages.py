import logging
import traceback
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from discord_webhook import DiscordEmbed, DiscordWebhook

from src.domain.models import HealthSummary, HrvMetrics, SleepMetrics
from src.infra.time_provider import TimeProvider

logger = logging.getLogger(__name__)



# Send message with exception stack trace
class DiscordErrorMessage(DiscordEmbed):
    def __init__(self, error_message: str):
        super().__init__(
            title=f"⚠ Error ⚠",
            description=f"```{error_message}```",
            color=0xFF0000,
        )


# Health summary discord dto/message
class DiscordHealthSummaryMessage(DiscordEmbed):
    def __init__(self, health_summary: HealthSummary):

        title = f"Garmin Health Metrics, {health_summary.date.strftime('%d-%m-%Y')}"
        msg = ""

        # Sleep
        msg += self.create_sleep(health_summary.sleep)
        # Hrv
        msg += self.create_hrv(health_summary.hrv)

        super().__init__(
            title=title,
            description=msg,
            color=0x10A5E1,
        )

    def create_hrv(self, hrv_metrics: HrvMetrics) -> str:
        hrv_recent_str = hrv_metrics.current
        week_avg_str = hrv_metrics.weekly_avg
        diff_to_avg_str = (
            _val_to_signed_str(hrv_metrics.current_diff_to_average)
            if hrv_metrics.current_diff_to_average
            else "N/A"
        )

        return f"```💓 HRV: {hrv_recent_str} (weekly avg: {week_avg_str}, Δ avg: {diff_to_avg_str})```"

    def create_sleep(self, sleep_metrics: SleepMetrics) -> str:
        sleep_recent_str = _format_timedelta(sleep_metrics.current)
        week_avg_str = _format_timedelta(sleep_metrics.avg)
        diff_to_avg_str = _format_timedelta(
            sleep_metrics.diff_to_average, should_include_sign=True
        )
        diff_to_8h_str = _format_timedelta(
            sleep_metrics.get_diff_to_hour(8), should_include_sign=True
        )

        return f"```💤 Sleep: {sleep_recent_str} (weekly avg: {week_avg_str}, Δ avg: {diff_to_avg_str}, Δ 8h: {diff_to_8h_str})```"


def _val_to_signed_str(value: float) -> str:
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