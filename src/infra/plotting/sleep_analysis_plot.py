import datetime
import logging
from enum import Enum
from typing import NamedTuple, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import numpy.typing as npt
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.gridspec import GridSpec
from matplotlib.patches import FancyBboxPatch
from mpl_toolkits.axes_grid1 import make_axes_locatable  # type: ignore

from src.consts import DAYS_IN_WEEK, SECONDS_IN_HOUR
from src.domain.metrics import SleepMetrics, SleepScoreMetrics

logger = logging.getLogger(__name__)

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


# Create plot with 3 subplots:
# Row 1 (1 plot): Sleep stages for the last 7 days
# Row 2 (2 plots):
# - 7-day moving average stacked area chart for each sleep stage for the last 4 weeks
# - Sleep score waffle chart for the last 4 weeks
def plot(
    sleep: SleepMetrics,
    sleep_score: SleepScoreMetrics,
    ma_window_size: int,  # Window size of moving average
):
    fig = plt.figure(figsize=(12, 9))
    gs = GridSpec(2, 2, width_ratios=[1, 0.5], height_ratios=[3, 2])
    week_plot = plt.subplot(gs[0, :])  # merge columns in this row
    four_weeks_plot = plt.subplot(gs[1, 0])
    waffle_plot = plt.subplot(gs[1, 1])

    sleep_plotting_data = _transform_durations(sleep, ma_window_size)

    # Chart 1
    # Reduce to last 7 days
    week_data = sleep_plotting_data.get_last_n(DAYS_IN_WEEK)
    plot_week_durations(week_plot, week_data)
    score_plot: Axes = week_plot.twinx()  # type: ignore
    plot_scores_dot(score_plot, sleep_score, limit=DAYS_IN_WEEK)

    # Chart 2
    FOUR_WEEKS = 4 * DAYS_IN_WEEK
    four_weeks_data = sleep_plotting_data.get_last_n(FOUR_WEEKS)
    plot_moving_avg_durations(four_weeks_plot, four_weeks_data)
    plot_scores_line(
        four_weeks_plot,
        sleep_score,
        ma_window_size,
        limit=FOUR_WEEKS,
    )

    # Chart 3
    # _plot_waffle_chart_sleep_duration(waffle_plot, dto_sleep_duration)
    _plot_waffle_chart_sleep_score(waffle_plot, sleep_score)

    handles, labels = week_plot.get_legend_handles_labels()
    handles_score, labels_score = score_plot.get_legend_handles_labels()
    week_plot.legend(
        handles + handles_score,
        labels + labels_score,
        fontsize="small",
        loc="upper left",
    )

    fig.tight_layout()

    return fig


def plot_scores_line(
    full_plot: Axes,
    sleep_score: SleepScoreMetrics,
    ma_window_size: int,
    limit: int,
):
    # Get plot with sleep score on its own y-axis
    score_plot_ma: Axes = full_plot.twinx()  # type: ignore

    score_plot_ma.plot(
        [entry.calendarDate for entry in sleep_score.entries[-limit:]],  # type: ignore
        _get_moving_average(  # type: ignore
            [entry.value for entry in sleep_score.entries[-limit:]], ma_window_size
        ),
        color="black",
        label="Sleep Score",
    )

    score_plot_ma.set_ylabel("Sleep Score (0-100)", color="black")


def plot_scores_dot(score_plot: Axes, sleep_score: SleepScoreMetrics, limit: int):
    # Plot sleep score with its own y-axis
    line = score_plot.plot(
        [entry.calendarDate for entry in sleep_score.entries[-limit:]],  # type: ignore
        [entry.value for entry in sleep_score.entries[-limit:]],
        color="black",
        label="Sleep Score",
        marker="o",
        linestyle="None",
    )
    score_plot.set_ylabel("Sleep Score (0-100)")
    # score_plot.legend(fontsize="small", loc="upper left")

    return line


def plot_week_durations(week_plot: Axes, plotting_data: PlottingData):
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
    # week_plot.legend(fontsize="small", loc="upper left")

    week_plot.grid(axis="y", alpha=0.5, linestyle="--")


def plot_moving_avg_durations(plot: Axes, plotting_data: PlottingData):
    logger.debug(f"Plotting days in moving avg. plot: {len(plotting_data.dates)}")

    plot.stackplot(
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

    plot.set_title(f"7-Day Moving Average (Last {len(plotting_data.dates)} Days)")

    plot.set_ylabel("Sleep Hours")

    plot.grid(axis="y", alpha=0.5, linestyle="--")

    fmt = mdates.DateFormatter("%d/%m")
    plot.xaxis.set_major_formatter(fmt)


# Tranform into suitable plotting data
def _transform_durations(sleep: SleepMetrics, window_size: int) -> PlottingData:
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

    dates = [entry.calendarDate for entry in sleep.entries]

    values = [
        entry.values.deepSleepSeconds / SECONDS_IN_HOUR for entry in sleep.entries
    ]
    deep_sleep = Segment(
        name=SegmentNames.DEEP.value,
        color=Colors.DEEP.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )

    values = [
        entry.values.lightSleepSeconds / SECONDS_IN_HOUR for entry in sleep.entries
    ]
    light_sleep = Segment(
        name=SegmentNames.LIGHT.value,
        color=Colors.LIGHT.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )

    values = [entry.values.REMSleepSeconds / SECONDS_IN_HOUR for entry in sleep.entries]
    rem_sleep = Segment(
        name=SegmentNames.REM.value,
        color=Colors.REM.value,
        values=values,
        values_ma=_get_moving_average(values, window_size),
    )

    values = [
        entry.values.awakeSleepSeconds / SECONDS_IN_HOUR for entry in sleep.entries
    ]
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


def _plot_waffle_chart_sleep_score(ax: Axes, model: SleepScoreMetrics):
    sleep_data = np.array(
        [entry.value for entry in model.entries],
        dtype=float,
    )

    start_day = model.entries[0].calendarDate.weekday()

    # Number of complete weeks and remaining days
    adjusted_weeks = adjust_weeks(sleep_data, start_day)

    # XXX: RdYlBu produces very distinct colors, I think this is the best one
    colormap: LinearSegmentedColormap = plt.cm.RdYlBu  # type: ignore

    # XXX: This colormap produces less distinct colors
    # colors_solid_red_yellow_green = [(1, 0.2, 0), (1, 1, 0), (0, 0.8, 0)]  # Solid R -> Solid Y -> Solid G
    # colormap = LinearSegmentedColormap.from_list('custom_solid_red_yellow_green', colors_solid_red_yellow_green, N=100)

    # set color for nan values
    # ax.set_facecolor("lightgrey")  # type: ignore
    # ax.set_facecolor("#F0F0F0")  # type: ignore

    padding = 0.4
    linewidth = 4
    color_background = "white"
    # background = "#F0F0F0"
    edgecolor = color_background

    # Create a custom normalization with the range of sleep scores (0 to 100)
    score_norm = Normalize(vmin=0, vmax=100, clip=True)
    for week_num in range(adjusted_weeks.shape[1]):
        for day_num in range(adjusted_weeks.shape[0]):
            sleep_score = adjusted_weeks[day_num, week_num]
            if not np.isnan(
                sleep_score
            ):  # Check if the value is not nan before drawing rectangle
                color = colormap(score_norm(sleep_score))  # type: ignore
                # rect = plt.Rectangle(  # type: ignore
                #     xy=(week_num, 6 - day_num),
                #     width=1,
                #     height=1,
                #     facecolor=color,  # type: ignore
                #     edgecolor="white",
                #     linewidth=0.8,
                # )

                rect = FancyBboxPatch(
                    (week_num + padding / 2, DAYS_IN_WEEK - 1 - day_num + padding / 2),
                    1 - padding,
                    1 - padding,
                    boxstyle="round,pad=" + str(padding / 2),
                    facecolor=color,  # type: ignore
                    edgecolor=edgecolor,
                    linewidth=linewidth,
                )
                ax.add_patch(rect)

    # Set axis limits and labels
    ax.set_xlim(0, adjusted_weeks.shape[1])
    ax.set_ylim(0, adjusted_weeks.shape[0])
    ax.set_xlabel("Weeks")
    ax.set_title(f"Sleep Scores (Last {len(sleep_data)} Days)")

    # set x ticks such that they are in the middle of the week
    ax.set_xticks(np.arange(0.5, adjusted_weeks.shape[1] + 0.5, 1))
    ax.set_xticklabels(np.arange(1, adjusted_weeks.shape[1] + 1, 1))

    # Remove border
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # Also remove the ticks on the x-axis
    ax.tick_params(axis="both", which="both", length=0)

    # Set y-axis labels
    ax.set_yticks([0.5, 6.5])
    ax.set_yticklabels(["Sun", "Mon"])

    ax.set_facecolor(color_background)  # type: ignore
    # ax.set_facecolor("red")  # type: ignore

    # Remove gridlines
    ax.grid(False)

    # Add colorbar with the RdYlBu colormap and score normalization
    # Adjust colorbar width with increased size
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="10%", pad=0.2)  # size = Width of colorbar
    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=colormap, norm=score_norm), cax=cax)  # type: ignore
    cbar.set_label("Sleep Score (0-100)")

    # Set custom ticks and labels on the colorbar
    cbar_ticks = [0, 25, 50, 75, 100]
    cbar_labels = ["0", "25", "50", "75", "100"]
    cbar.set_ticks(cbar_ticks)
    cbar.set_ticklabels(cbar_labels)

    # Place plot in the center
    ax.set_anchor("C")

    # Adjust aspect ratio such that each rectangle is square shaped
    ax.set_aspect("equal")


def adjust_weeks(sleep_data: npt.NDArray[np.float64], start_day: int):
    num_weeks = (len(sleep_data) + start_day) // DAYS_IN_WEEK
    adjusted_weeks = np.full((num_weeks + 1, DAYS_IN_WEEK), np.nan)

    day_indices = np.arange(len(sleep_data)) + start_day
    week_indices = day_indices // DAYS_IN_WEEK
    day_positions = day_indices % DAYS_IN_WEEK

    adjusted_weeks[week_indices, day_positions] = sleep_data

    return adjusted_weeks.T


# XXX: Waffle chart for sleep duration not used ATM. -> Refactor to use same code as sleep score if needed
# Creates a waffle chart of the values
def _plot_waffle_chart_sleep_duration(plot: Axes, dto: SleepMetrics):
    sleep_data = np.array(
        [entry.values.totalSleepSeconds / SECONDS_IN_HOUR for entry in dto.entries],
        dtype=float,
    )

    # Number of complete weeks and remaining days
    num_weeks = len(sleep_data) // DAYS_IN_WEEK
    remaining_days = len(sleep_data) % DAYS_IN_WEEK

    # Create an array with shape (num_weeks + 1, 7), and fill it with nan
    adjusted_weeks = np.full((num_weeks + 1, DAYS_IN_WEEK), np.nan)

    # Fill the adjusted_weeks array with the sleep data
    adjusted_weeks[:num_weeks, :] = sleep_data[: num_weeks * DAYS_IN_WEEK].reshape(
        num_weeks, DAYS_IN_WEEK
    )
    adjusted_weeks[num_weeks, :remaining_days] = sleep_data[
        num_weeks * DAYS_IN_WEEK : num_weeks * DAYS_IN_WEEK + remaining_days
    ]

    # Transpose the array to have days as rows and weeks as columns
    adjusted_weeks = adjusted_weeks.T

    # Define a transition point for the colormap
    transition_point = 8.0

    # Get the RdYlBu colormap
    rdylbu = plt.cm.RdYlBu  # type: ignore

    # Extract colors that correspond to 0 to 8 hours from the RdYlBu colormap
    colors_for_0_to_8 = rdylbu(np.linspace(0, 1, int(256 * (transition_point / 12.0))))  # type: ignore

    # Generate a gradient of colors from the color corresponding to 8 hours to black for 8 to 12 hours
    colors_for_8_to_12 = np.linspace(  # type: ignore
        colors_for_0_to_8[-1], [0, 0, 0, 1], 256 - len(colors_for_0_to_8)  # type: ignore
    )

    # Concatenate the two sets of colors to form the new colormap
    final_colors = np.vstack((colors_for_0_to_8, colors_for_8_to_12))  # type: ignore

    # Create the new colormap
    final_cmap = LinearSegmentedColormap.from_list("RdYlBu_Black", final_colors)  # type: ignore

    # Create a custom normalization with the original range of sleep data
    new_norm = Normalize(vmin=0, vmax=12, clip=True)

    # Create the visualization with the final colormap
    # fig, ax = plt.subplots(figsize=(15, 7))

    for week in range(adjusted_weeks.shape[1]):
        for day in range(adjusted_weeks.shape[0]):
            sleep_duration = adjusted_weeks[day, week]
            if not np.isnan(
                sleep_duration
            ):  # Check if the value is not nan before drawing rectangle
                color = final_cmap(new_norm(sleep_duration))  # type: ignore
                rect = plt.Rectangle(  # type: ignore
                    (week, 6 - day),
                    1,
                    1,
                    facecolor=color,  # type: ignore
                    edgecolor="white",
                    linewidth=0.5,
                )
                plot.add_patch(rect)

    # Set axis limits and labels
    plot.set_xlim(0, adjusted_weeks.shape[1])
    plot.set_ylim(0, adjusted_weeks.shape[0])
    plot.set_xlabel("Weeks")
    plot.set_title(f"Sleep Duration (Last {len(sleep_data)} Days)")

    # Set y-axis labels
    plot.set_yticks([0.5, 6.5])  # For centering the labels
    plot.set_yticklabels(["Sunday", "Monday"])

    # Remove gridlines
    plot.grid(False)

    # Add colorbar with the final colormap and normalization
    cbar = plt.colorbar(plt.cm.ScalarMappable(cmap=final_cmap, norm=new_norm), ax=plot)
    cbar.set_label("Sleep Duration (hours)")

    # Set custom ticks and labels on the colorbar
    cbar_ticks = [0, 4, 8, 12]  # Define the tick positions
    cbar_labels = ["0", "4", "8", "12+"]  # Define the tick labels
    cbar.set_ticks(cbar_ticks)  # Set the tick positions on the colorbar
    cbar.set_ticklabels(cbar_labels)  # Set the tick labels on the colorbar

    # Place plot in the center by setting anchor
    plot.set_anchor("C")
    cbar.ax.set_anchor("W")

    # Adjust aspect ratio
    plot.set_aspect("equal")
