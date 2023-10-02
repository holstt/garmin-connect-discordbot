import datetime
import logging
from enum import Enum
from typing import NamedTuple, Optional

import matplotlib.dates as mdates
from matplotlib import pyplot as plt
from matplotlib.axes import Axes

from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse

logger = logging.getLogger(__name__)

SECONDS_IN_HOUR = 60 * 60

# ALPHA = 0.7


class Colors(Enum):
    DEEP = "#004BA0"
    LIGHT = "#1976D2"
    REM = "#AC06BC"
    AWAKE = "#ED79D5"


class SegmentNames(Enum):
    DEEP = "Deep sleep"
    LIGHT = "Light Sleep"
    REM = "Rem Sleep"
    AWAKE = "Awake Sleep"


class Segment(NamedTuple):
    name: str
    color: str
    values: list[float]
    values_ma: list[Optional[float]]


class PlottingData(NamedTuple):
    dates: list[datetime.date]
    segments: list[Segment]

    def get_last_n(self, n: int):
        return PlottingData(
            dates=self.dates[-n:],
            segments=[
                Segment(
                    name=segment.name,
                    color=segment.color,
                    values=segment.values[-n:],
                    values_ma=segment.values_ma[-n:],
                )
                for segment in self.segments
            ],
        )


def plot(
    dto_sleep_duration: GarminSleepResponse,
    dto_sleep_score: GarminSleepScoreResponse,
    ma_window_size: int,  # Window size of moving average
):
    # Create plot with 2 subplots horizontally stacked with different heights
    # First plot shows sleep stages for the last 7 days
    # Second plot shows the 7-day moving average for each sleep stage for the last 4 weeks.

    fig, (week_plot, full_plot) = plt.subplots(
        2, 1, figsize=(12, 9), gridspec_kw={"height_ratios": [3, 1]}
    )

    week_plot: Axes
    full_plot: Axes

    duration_plotting_data = _transform_durations(dto_sleep_duration, ma_window_size)

    plot_week_durations(week_plot, duration_plotting_data)
    plot_week_scores(week_plot, dto_sleep_score)
    plot_full_durations(full_plot, duration_plotting_data)
    plot_full_scores(
        full_plot,
        dto_sleep_score,
        ma_window_size,
    )
    fig.tight_layout()

    return fig


def plot_full_scores(
    full_plot: Axes, dto_sleep_score: GarminSleepScoreResponse, ma_window_size: int
):
    # Get plot with sleep score on its own y-axis
    score_plot_ma: Axes = full_plot.twinx()  # type: ignore

    score_plot_ma.plot(
        [entry.calendarDate for entry in dto_sleep_score.entries],  # type: ignore
        _get_moving_average(  # type: ignore
            [entry.value for entry in dto_sleep_score.entries], ma_window_size
        ),
        color="black",
        label="Sleep Score",
    )


def plot_week_scores(week_plot: Axes, dto_sleep_score: GarminSleepScoreResponse):
    score_plot: Axes = week_plot.twinx()  # type: ignore
    # Plot sleep score with its own y-axis
    score_plot.plot(
        [entry.calendarDate for entry in dto_sleep_score.entries[-7:]],  # type: ignore
        [entry.value for entry in dto_sleep_score.entries[-7:]],
        color="black",
        label="Sleep Score",
        marker="o",
        linestyle="None",
    )
    score_plot.set_ylabel("Sleep Score (0-100)", color="black")
    score_plot.legend()


def plot_week_durations(week_plot: Axes, plotting_data: PlottingData):
    # Reduce to last 7 days
    plotting_data = plotting_data.get_last_n(7)

    # Keep track of current bottom of each bar
    bar_bottoms = [0] * len(plotting_data.dates)

    # Iterate each stress segment and plot all bars for that segment
    for segment in plotting_data.segments:
        bar = week_plot.bar(
            x=plotting_data.dates,  # type: ignore
            height=segment.values,
            color=segment.color,
            bottom=bar_bottoms,
            label=segment.name,
            # alpha=ALPHA,
            # width=bar_width,
        )
        # Add current segment values to the bar buttoms
        bar_bottoms = [sum(x) for x in zip(bar_bottoms, segment.values)]

    # Add 8-hour target line
    week_plot.axhline(y=8, color="r", linestyle="--", label="8-hour Target")

    # Add bar value to the top of each bar
    bars = week_plot.containers  # type: ignore
    week_plot.bar_label(bars[-1], fmt="%.1f")  # type: ignore

    # Set the formatter for x-axis to display both day name and day/month
    formatter = mdates.DateFormatter("%A\n%d/%m")
    week_plot.xaxis.set_major_formatter(formatter)

    week_plot.set_title(f"Sleep Stages (Last {len(plotting_data.dates)} Days)")
    week_plot.set_ylabel("Sleep Hours")
    week_plot.legend(fontsize="small", loc="upper left")

    week_plot.grid(axis="y", alpha=0.5, linestyle="--")


def plot_full_durations(full_plot: Axes, plotting_data: PlottingData):
    logger.debug(f"Plotting days in full plot: {plotting_data.dates}")

    full_plot.stackplot(
        # x axis is dates that where moving average is not None (i.e. not the first n days). We use the first segment, but should be the same for all
        [date for date, ma in zip(plotting_data.dates, plotting_data.segments[0].values_ma) if ma],  # type: ignore
        # y axis is the list of not None moving averages for each segment
        [
            [val_ma for val_ma in segment.values_ma if val_ma]
            for segment in plotting_data.segments
        ],
        colors=[segment.color for segment in plotting_data.segments],
        labels=[segment.name for segment in plotting_data.segments],
    )

    full_plot.set_title(f"7-Day Moving Average (Last {len(plotting_data.dates)} Days)")

    full_plot.set_ylabel("Sleep Hours")

    full_plot.grid(axis="y", alpha=0.5, linestyle="--")


# Tranform into suitable plotting data
def _transform_durations(dto: GarminSleepResponse, window_size: int) -> PlottingData:
    # Calculation for normalizing sleep data (not used atm)
    # def sum_durations(entry: SleepEntry):
    #     valid_durations = [
    #         entry.values.deepSleepSeconds,
    #         entry.values.lightSleepSeconds,
    #         entry.values.REMSleepSeconds,
    #         entry.values.awakeSleepSeconds,
    #     ]
    #     return sum([duration for duration in valid_durations if duration])

    # max_total_sleep = max([sum_durations(entry) for entry in dto.entries])

    dates = [entry.calendarDate for entry in dto.entries]

    values = [entry.values.deepSleepSeconds / SECONDS_IN_HOUR for entry in dto.entries]
    deep_sleep = Segment(
        name=SegmentNames.DEEP.value,
        color=Colors.DEEP.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )

    values = [entry.values.lightSleepSeconds / SECONDS_IN_HOUR for entry in dto.entries]
    light_sleep = Segment(
        name=SegmentNames.LIGHT.value,
        color=Colors.LIGHT.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )

    values = [entry.values.REMSleepSeconds / SECONDS_IN_HOUR for entry in dto.entries]
    rem_sleep = Segment(
        name=SegmentNames.REM.value,
        color=Colors.REM.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )

    values = [entry.values.awakeSleepSeconds / SECONDS_IN_HOUR for entry in dto.entries]
    awake_sleep = Segment(
        name=SegmentNames.AWAKE.value,
        color=Colors.AWAKE.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )
    return PlottingData(
        dates=dates,
        segments=[deep_sleep, light_sleep, rem_sleep, awake_sleep],
    )


def _get_moving_average(values: list[float], window_size: int) -> list[Optional[float]]:
    moving_averages: list[Optional[float]] = []

    for i in range(1, len(values) + 1):
        if i < window_size:
            moving_averages.append(None)
        else:
            moving_averages.append(sum(values[i - window_size : i]) / window_size)
    return moving_averages
