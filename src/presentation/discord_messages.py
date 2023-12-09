import enum
import logging
from datetime import date
from typing import Sequence

from discord_webhook import DiscordEmbed
from table2ascii import Alignment, PresetStyle, table2ascii

import src.presentation.view_models as view_models
from src.presentation.view_models import HealthSummaryViewModel, MetricViewModel

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
class DiscordMessageBase(DiscordEmbed):
    def __init__(self, date: date, description: str):
        title = f"Garmin Health Metrics, {date.strftime('%d-%m-%Y')}"
        super().__init__(
            title=title,
            description=description,
            color=0x10A5E1,
        )


# Creates a discord message with metrics in a table
class DiscordMessageTable(DiscordMessageBase):
    def __init__(self, summary: HealthSummaryViewModel):
        view_models = summary.metrics
        style = PresetStyle.borderless

        header = ["", "Value", "Δ Avg", "Week Avg", "Metric", "Δ Target"]
        alignments = [
            Alignment.RIGHT,
            Alignment.RIGHT,
            Alignment.RIGHT,
            Alignment.RIGHT,
            Alignment.LEFT,
            Alignment.LEFT,
        ]
        body = []
        for idx, view_model in enumerate(view_models):
            body.append(self._to_table_row(view_model))
            body.append([""] * len(header))
        table = table2ascii(header, body, style=style, alignments=alignments)

        table = f"```{table}```"
        super().__init__(summary.date, table)

    def _to_table_row(self, view_model: MetricViewModel) -> Sequence[str]:
        return [
            view_model.icon,
            f"{view_model.latest}{view_model.out_of_max}",
            f"{view_model.diff_to_avg} {view_model.diff_to_avg_emoji}",
            f"{view_model.week_avg}{view_model.out_of_max}",
            view_model.name,
            # Avoid including target name. Will result in too long table row messing up the table
            f"{view_model.diff_to_target.diff}"
            # f"{view_model.diff_to_target.target_name}: {view_model.diff_to_target.diff}"
            if view_model.diff_to_target else "",
        ]


# Creates a discord message with metrics in a list
class DiscordMessageLines(DiscordMessageBase):
    def __init__(self, summary: HealthSummaryViewModel):
        view_models = summary.metrics
        lines = ""
        for i, view_model in enumerate(view_models):
            lines += self._to_line(view_model)
            # Add newline for every two metrics
            if i % 2 == 1:
                lines += "\n"
        super().__init__(summary.date, lines)

    def _to_line(self, view_model: MetricViewModel) -> str:
        diff_to_target_str = (
            f", Δ {view_model.diff_to_target.target_name}: {view_model.diff_to_target.diff}"
            if view_model.diff_to_target
            else ""
        )
        return f"```{view_model.icon} {view_model.name}: {view_model.latest}{view_model.out_of_max} - (weekly avg: {view_model.week_avg}{view_model.out_of_max}, Δ avg: {view_model.diff_to_avg}{diff_to_target_str})```"


# XXX: Not used atm. Maybe relevant if we change the table style
# def replace_horizontal_lines_except_first_last(table_str: str) -> str:
#     lines = table_str.split("\n")
#     for i in range(1, len(lines) - 1):  # Skip the first and last lines
#         lines[i] = lines[i].replace("─", "-")
#     return "\n".join(lines)


# def remove_top_and_bottom_lines(table_str: str) -> str:
#     lines = table_str.split("\n")
#     return "\n".join(lines[1:-1])  # Skip the first and last lines
