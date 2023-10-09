from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import src.infra.plotting.metrics_gridplot as metrics_gridplot
import src.infra.plotting.sleep_analysis_plot as sleep_analysis_plot
from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)


def get_last_n(
    metric: GarminResponseDto[GarminResponseEntryDto], n: int
) -> GarminResponseDto[GarminResponseEntryDto]:
    return type(metric)(metric.entries[-n:])


def create_metrics_gridplot(
    metrics: list[GarminResponseDto[GarminResponseEntryDto]],
    n: int | None = None,
) -> BytesIO:
    # TODO: Return None if no data

    if n:
        metrics = [get_last_n(metric, n) for metric in metrics]

    fig = metrics_gridplot.plot(metrics)
    buf = save_plot_to_buffer(fig)
    return buf


def create_sleep_analysis_plot(
    sleep: metrics_gridplot.GarminSleepResponse,
    sleep_score: metrics_gridplot.GarminSleepScoreResponse,
    ma_window_size: int,
) -> BytesIO:
    fig = sleep_analysis_plot.plot(sleep, sleep_score, ma_window_size)
    buf = save_plot_to_buffer(fig)
    return buf


def save_plot_to_buffer(fig: Figure):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf
