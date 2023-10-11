from datetime import date
from typing import Any, NamedTuple, Sequence

import numpy as np
import numpy.typing as npt
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure

from src.consts import SECONDS_IN_HOUR
from src.domain.metrics import (
    BaseMetric,
    BbMetrics,
    HrvMetrics,
    RhrMetrics,
    SleepMetrics,
    SleepScoreMetrics,
    StressMetrics,
)
from src.infra.garmin.dtos.garmin_response import GarminResponseEntryDto
from src.utils import get_moving_average

PLOT_SIZE = (8, 9)


class _GridPlotMetric(NamedTuple):
    name: str
    color: str
    values: Sequence[float | None]

    def get_avg(self) -> float:
        return sum([val for val in self.values if val]) / len(self.values)


# Creates subplot for each metric in a single figure
def plot(
    metrics_data: Sequence[BaseMetric[GarminResponseEntryDto, Any]],
) -> Figure:
    # Just get the dates from one of the metrics (they should all be the same)
    dates = [entry.calendarDate for entry in metrics_data[0].entries]
    weekdays = [date.strftime("%a") for date in dates]

    plot_metrics = _transform(metrics_data)

    fig = plt.figure(figsize=PLOT_SIZE)

    COLS = 2
    ROWS = (
        len(plot_metrics) // COLS
        if len(plot_metrics) % COLS == 0
        else len(plot_metrics) // COLS + 1
    )

    for idx, plot_metric in enumerate(plot_metrics, start=1):
        ax = plt.subplot(ROWS, COLS, idx)
        _add_subplot(dates, weekdays, plot_metric, ax)

    plt.suptitle(f"Health Metrics (Last {len(dates)} days)", fontsize=16)
    plt.tight_layout()

    return fig


def _add_subplot(
    dates: Sequence[date],
    weekdays: Sequence[str],
    plot_metric: _GridPlotMetric,
    ax: Axes,
):
    # _plot_with_colormap(plot_metric, dates, ax)

    # Plot metric values as line chart
    ax.plot(dates, plot_metric.values, color=plot_metric.color, linestyle="-", marker="o", markersize=8)  # type: ignore

    # Format latest metric on chart such that marker is larger and has a black outline
    latest_date = dates[-1]
    latest_val = plot_metric.values[-1]
    ax.plot(latest_date, latest_val, color=plot_metric.color, marker="o", linestyle="", markersize=12)  # type: ignore
    ax.plot(latest_date, latest_val, color=plot_metric.color, marker="o", markeredgewidth=2, markeredgecolor="black", linestyle="", markersize=12)  # type: ignore

    # Add horizontal line with the metric average
    avg_value = plot_metric.get_avg()
    ax.axhline(
        y=avg_value, color="gray", linestyle="--", label=f"Average: {avg_value:.1f}"
    )

    # Add "background" line with full metric values #XXX: Not used atm - not sure if it's useful
    # _add_background_plot(plot_metric, ax, plot_metric_full)

    # Remove top and right spines
    # ax.spines["top"].set_visible(False)
    # ax.spines["right"].set_visible(False)

    # Configure chart
    ax.set_title(plot_metric.name)
    ax.set_xticks(dates, weekdays)  # type: ignore
    ax.legend()
    # ax.grid(True)
    # make grid lines more transparent
    ax.grid(alpha=0.50)


def _add_background_plot(
    plot_metric: _GridPlotMetric, ax: Axes, plot_metric_full: _GridPlotMetric
):
    ax_background: Axes = ax.twiny()  # type: ignore

    # Keep existing axis limits
    vals = [val for val in plot_metric.values if val]
    min_val = min(vals)
    max_val = max(vals)
    val_range = max_val - min_val
    padding = (
        val_range * 0.2
    )  # Adjust padding of foreground plot. Larger values will ensure more of the background plot is visible
    plt.ylim(
        min_val - padding,
        max_val + padding,
    )

    # Now calculate the 7-day moving average for the full values
    MA_SIZE = 7
    # TODO: Use prev val if possible
    plot_metric_full_no_none: Sequence[float] = [
        val if val else 0 for val in plot_metric_full.values
    ]
    moving_avgs = get_moving_average(plot_metric_full_no_none, MA_SIZE)

    ax_background.plot(
        range(len(moving_avgs)),
        moving_avgs,  # type: ignore
        color=plot_metric.color,
        alpha=0.25,
    )


def _transform(metrics_data: Sequence[BaseMetric[GarminResponseEntryDto, Any]]):
    return [get_plot_data(metric) for metric in metrics_data]


# TODO: Refactor
# TODO: Move representation of each metric to setup/plugin pattern
def get_plot_data(metric: BaseMetric[GarminResponseEntryDto, Any]) -> _GridPlotMetric:
    if isinstance(metric, SleepMetrics):
        return _GridPlotMetric(
            name="Sleep",
            color="#2ca02c",
            values=[
                entry.values.totalSleepSeconds / SECONDS_IN_HOUR
                for entry in metric.entries
            ],
        )
    if isinstance(metric, RhrMetrics):
        return _GridPlotMetric(
            name="Resting Heart Rate",
            color="#d62728",
            values=[entry.values.restingHR for entry in metric.entries],
        )
    if isinstance(metric, StressMetrics):
        return _GridPlotMetric(
            name="Stress Level",
            color="#8c564b",
            values=[entry.values.overallStressLevel for entry in metric.entries],
        )
    if isinstance(metric, BbMetrics):
        return _GridPlotMetric(
            name="Body Battery",
            color="#e377c2",
            values=[
                max([val for (time, val) in entry.bodyBatteryValuesArray])
                for entry in metric.entries
            ],
        )
    if isinstance(metric, SleepScoreMetrics):
        return _GridPlotMetric(
            name="Sleep Score",
            color="#9467bd",
            values=[entry.value for entry in metric.entries],
        )
    if isinstance(metric, HrvMetrics):
        return _GridPlotMetric(
            name="HRV",
            color="#7f7f7f",
            values=[entry.lastNightAvg for entry in metric.entries],
        )

    raise ValueError(f"Unknown metric: {metric}")

    # TODO:
    # case GarminStepsResponse(entries):
    #     return _GridPlotMetric(
    #         name="Steps",
    #         color="#1f77b4",
    #         values=[entry.totalSteps for entry in entries],
    #     )
    # MetricObj(name='Intensity Minutes', color='#ff7f0e', range=(0, 120)),


# XXX: Not used. Solid colors seem to be better?
def _plot_with_colormap(plot_metric: _GridPlotMetric, dates: Sequence[date], ax: Axes):
    values: npt.NDArray[np.float64] = np.array(plot_metric.values, dtype=np.float64)

    # Create a linear segmented colormap from white to the input hex color
    custom_cmap = LinearSegmentedColormap.from_list(
        "custom_cmap", ["white", plot_metric.color], N=256
    )

    # normalize between 0 and 1, using the min and max values of the data
    normalized_vals = (values - min(values)) / (max(values) - min(values))

    # Get the colors for each data point from the custom colormap
    point_colors_custom = custom_cmap(normalized_vals)  # type: ignore

    num_days = len(dates)

    # Plot the generated RHR data with custom colormap and circle markers
    for i in range(num_days - 1):
        ax.plot(
            dates[i : i + 2],  # type: ignore
            values[i : i + 2],
            color=custom_cmap((normalized_vals[i] + normalized_vals[i + 1]) / 2),  # type: ignore
        )

    # Scatter plot with custom colors and circle markers
    ax.scatter(
        dates,  # type: ignore
        values,
        color=point_colors_custom,  # type: ignore
        s=100,
        zorder=5,
        marker="o",
        edgecolors="k",
    )

    # plt.colorbar(
    #     ScalarMappable(cmap=custom_cmap), label="Resting Heart Rate (bpm)", ax=ax
    # )
