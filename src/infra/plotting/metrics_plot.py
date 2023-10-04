from datetime import date
from typing import NamedTuple, Optional

import numpy as np
import numpy.typing as npt
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.colors import LinearSegmentedColormap

import src.infra.garmin.dtos as dtos
from src.infra.garmin.dtos.garmin_bb_response import GarminBbResponse
from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_rhr_response import GarminRhrResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.garmin.dtos.garmin_steps_response import GarminStepsResponse
from src.infra.garmin.dtos.garmin_stress_response import GarminStressResponse

# type_to_color = {
#     dtos.GarminSleepResponse: "red",
#     dtos.GarminSleepScoreResponse: "blue",
#     dtos.GarminBbResponse: "green",
#     dtos.GarminRhrResponse: "yellow",
#     dtos.GarminStepsResponse: "purple",
#     dtos.GarminStressResponse: "orange",
#     dtos.GarminHrvResponse: "pink",
# }


SECONDS_IN_HOUR = 3600


class MetricsData(NamedTuple):
    sleep: dtos.GarminSleepResponse
    sleep_score: dtos.GarminSleepScoreResponse
    bb: dtos.GarminBbResponse
    rhr: dtos.GarminRhrResponse
    # steps: dtos.GarminStepsResponse
    stress: dtos.GarminStressResponse
    hrv: dtos.GarminHrvResponse

    def get_last_n(self, n: int):
        return MetricsData(
            GarminSleepResponse(self.sleep.entries[-n:]),
            GarminSleepScoreResponse(self.sleep_score.entries[-n:]),
            GarminBbResponse(self.bb.entries[-n:]),
            GarminRhrResponse(self.rhr.entries[-n:]),
            # GarminStepsResponse(self.steps.entries[-n:]),
            GarminStressResponse(self.stress.entries[-n:]),
            GarminHrvResponse(hrvSummaries=self.hrv.entries[-n:], userProfilePk=0),
        )


class MetricPlot(NamedTuple):
    name: str
    color: str
    values: list[Optional[float]]


# Creates subplot for each metric in a single figure
def plot(metrics_data: MetricsData):
    plot_data = _transform(metrics_data)

    # Just get the dates from one of the metrics (they should all be the same)
    dates = [entry.calendarDate for entry in metrics_data.bb.entries]
    weekdays = [date.strftime("%a") for date in dates]

    fig = plt.figure(figsize=(11, 13))

    COLS = 2
    ROWS = (
        len(plot_data) // COLS
        if len(plot_data) % COLS == 0
        else len(plot_data) // COLS + 1
    )

    for idx, plot_metric in enumerate(plot_data, start=1):
        ax = plt.subplot(ROWS, COLS, idx)
        _add_subplot(dates, weekdays, plot_metric, ax)

    plt.suptitle(f"Health Metrics (Last {len(dates)} days)", fontsize=16)
    plt.tight_layout()

    return fig


def _add_subplot(
    dates: list[date], weekdays: list[str], plot_metric: MetricPlot, ax: Axes
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
    avg_value = sum([val for val in plot_metric.values if val]) / len(
        plot_metric.values
    )
    ax.axhline(
        y=avg_value, color="gray", linestyle="--", label=f"Average: {avg_value:.0f}"
    )

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


def _transform(metrics_data: MetricsData):
    plot_data = [
        # MetricPlot(
        #     name="Steps",
        #     color="#1f77b4",
        #     values=[entry.totalSteps for entry in metrics_data.steps.entries],
        # ),
        # MetricObj(name='Intensity Minutes', color='#ff7f0e', range=(0, 120)),
        MetricPlot(
            name="Sleep Duration",
            color="#2ca02c",
            values=[
                entry.values.totalSleepSeconds / SECONDS_IN_HOUR
                for entry in metrics_data.sleep.entries
            ],
        ),
        MetricPlot(
            name="Sleep Score",
            color="#9467bd",
            values=[entry.value for entry in metrics_data.sleep_score.entries],
        ),
        MetricPlot(
            name="Resting Heart Rate",
            color="#d62728",
            values=[entry.values.restingHR for entry in metrics_data.rhr.entries],
        ),
        MetricPlot(
            name="Stress Level",
            color="#8c564b",
            values=[
                entry.values.overallStressLevel for entry in metrics_data.stress.entries
            ],
        ),
        MetricPlot(
            name="Body Battery",
            color="#e377c2",
            values=[
                max([val for (time, val) in entry.bodyBatteryValuesArray])
                for entry in metrics_data.bb.entries
            ],
        ),
        MetricPlot(
            name="HRV",
            color="#7f7f7f",
            values=[entry.lastNightAvg for entry in metrics_data.hrv.entries],
        ),
    ]

    return plot_data


# XXX: Not used. Solid colors seem to be better?
def _plot_with_colormap(plot_metric: MetricPlot, dates: list[date], ax: Axes):
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
