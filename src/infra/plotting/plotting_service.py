from io import BytesIO
from typing import Any, Sequence

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

matplotlib.use("agg")

import src.infra.plotting.metrics_gridplot as metrics_gridplot
import src.infra.plotting.sleep_analysis_plot as sleep_analysis_plot
from src.domain.metrics import BaseMetric, SleepMetrics, SleepScoreMetrics
from src.infra.garmin.dtos.garmin_response import (
    GarminResponseDto,
    GarminResponseEntryDto,
)


def create_metrics_gridplot(
    metrics: Sequence[BaseMetric[GarminResponseEntryDto, Any]],
    n: int | None = None,
) -> BytesIO:
    # TODO: Return None if no data
    if n:
        metrics = [metric.with_last_n(n) for metric in metrics]

    if len(metrics) == 0:
        raise ValueError("No metrics to plot")

    fig = metrics_gridplot.plot(metrics)
    buf = save_plot_to_buffer(fig)
    return buf


def create_sleep_analysis_plot(
    sleep: SleepMetrics,
    sleep_score: SleepScoreMetrics,
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
