import enum
import logging
import re
from typing import Callable

from attr import has
from discord_webhook import DiscordEmbed
from table2ascii import Alignment, PresetStyle, table2ascii

import src.presentation.message_builder as builder
from src.presentation.view_models import HealthSummaryViewModel

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
    LINES = "lines"
    TABLE = "table"


# Health summary discord dto/message
# TODO: A MessageStrategy creates a discord message given a HealthSummaryViewModel. Strategy is chosen based on the loaded user config and injected into relevant discord message service
# i.e. --> MessageStrategy = Callable[[HealthSummaryViewModel], DiscordEmbed]
class DiscordHealthSummaryMessage(DiscordEmbed):
    def __init__(self, summary: HealthSummaryViewModel, format: MessageFormat):
        title = f"Garmin Health Metrics, {summary.date.strftime('%d-%m-%Y')}"
        msg = ""

        match format:
            case MessageFormat.LINES:
                msg = _create_lines(msg, summary.metrics)
            case MessageFormat.TABLE:
                msg = _create_table(msg, summary.metrics)

        super().__init__(
            title=title,
            description=msg,
            color=0x10A5E1,
        )


# Greates a discord message with metrics in a list
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


# Creates a discord message with metrics in a table
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
