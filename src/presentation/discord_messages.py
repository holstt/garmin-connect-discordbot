import logging

from discord_webhook import DiscordEmbed

import src.presentation.metric_line_builder as builder
from src.domain.metrics import HealthSummary

logger = logging.getLogger(__name__)


# Send message with error
class DiscordErrorMessage(DiscordEmbed):
    def __init__(self, error_name: str, error_message: str):
        super().__init__(
            title=f"⚠ Error: {error_name}",
            description=f"```{error_message}```",
            color=0xFF0000,
        )


# Send message with exception stack trace
class DiscordExceptionMessage(DiscordEmbed):
    def __init__(self, exception: Exception, stack_trace: str):
        super().__init__(
            title=f"⚠ Exception: {type(exception).__name__}",
            description=f"**{exception}**\n\n ```{stack_trace}```",
            color=0xFF0000,
        )


# Health summary discord dto/message
class DiscordHealthSummaryMessage(DiscordEmbed):
    def __init__(self, summary: HealthSummary):
        title = f"Garmin Health Metrics, {summary.date.strftime('%d-%m-%Y')}"
        msg = ""

        msg += builder.sleep_line("Sleep", "💤", summary.sleep)
        msg += builder.metric_line("Sleep Score", "😴", summary.sleep_score, 100)
        msg += "\n"
        msg += builder.metric_line("Resting HR", "❤️", summary.rhr)
        msg += builder.hrv_line("HRV", "💓", summary.hrv)
        msg += "\n"
        msg += builder.metric_line("Body Battery (max today)", "⚡", summary.bb, 100)
        msg += builder.metric_line(
            "Stress Level (current overall)", "🤯", summary.stress, 100
        )
        super().__init__(
            title=title,
            description=msg,
            color=0x10A5E1,
        )
