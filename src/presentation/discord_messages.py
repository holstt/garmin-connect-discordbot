import enum
import logging
import re

from attr import has
from discord_webhook import DiscordEmbed
from table2ascii import Alignment, PresetStyle, table2ascii

import src.presentation.metric_msg_builder as builder
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


class MessageFormat(enum.Enum):
    LINES = 1
    TABLE = 2


# Health summary discord dto/message
class DiscordHealthSummaryMessage(DiscordEmbed):
    def __init__(
        self, summary: HealthSummary, format: MessageFormat = MessageFormat.LINES
    ):
        title = f"Garmin Health Metrics, {summary.date.strftime('%d-%m-%Y')}"
        msg = ""

        sleep = builder.sleep("Sleep", "💤", summary.sleep)
        sleep_score = builder.metric("Sleep Score", "😴", summary.sleep_score, 100)
        rhr = builder.metric(
            "Resting HR", "💗", summary.rhr
        )  # We do not use the regular heart emoji, as it seems to be more chars than the others and messes up the table alignment
        hrv = builder.hrv("HRV", "💓", summary.hrv)
        bb = builder.metric("Body Battery", "⚡", summary.bb, 100)
        stress = builder.metric("Stress Level", "🤯", summary.stress, 100)

        view_models = [sleep, sleep_score, rhr, hrv, bb, stress]

        if format == MessageFormat.LINES:
            msg = _create_lines(msg, view_models)
        else:
            msg = _create_table(msg, view_models)

        super().__init__(
            title=title,
            description=msg,
            color=0x10A5E1,
        )


def _create_lines(msg: str, view_models: list[builder.MetricViewModel]):
    for i, view_model in enumerate(view_models):
        msg += view_model.to_line()
        if i % 2 == 1:
            msg += "\n"
    return msg


# XXX: Not used atm. Maybe relevant if we change the table style
# def replace_horizontal_lines_except_first_last(table_str: str) -> str:
#     lines = table_str.split("\n")
#     for i in range(1, len(lines) - 1):  # Skip the first and last lines
#         lines[i] = lines[i].replace("─", "-")
#     return "\n".join(lines)


# def remove_top_and_bottom_lines(table_str: str) -> str:
#     lines = table_str.split("\n")
#     return "\n".join(lines[1:-1])  # Skip the first and last lines


def _create_table(msg: str, view_models: list[builder.MetricViewModel]):
    style = PresetStyle.borderless

    header = ["", "Value", "Δ Avg", "Week Avg", "Metric", "Δ Target"]
    alignments = [
        Alignment.RIGHT,
        Alignment.RIGHT,
        Alignment.RIGHT,
        Alignment.RIGHT,
        Alignment.LEFT,
        Alignment.RIGHT,
    ]
    body = []
    for idx, view_model in enumerate(view_models):
        body.append(view_model.to_table_row())
        body.append([""] * len(header))
    table = table2ascii(header, body, style=style, alignments=alignments)

    msg += table

    return f"```{msg}```"
