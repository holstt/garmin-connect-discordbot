import logging
from io import BytesIO
from typing import Any, Sequence

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

matplotlib.use("agg")

import src.infra.plotting.metrics_gridplot as metrics_gridplot
import src.infra.plotting.sleep_analysis_plot as sleep_analysis_plot
from src.domain.metrics import BaseMetric, SleepMetrics, SleepScoreMetrics
from src.infra.garmin.dtos.garmin_response import GarminResponseEntryDto

logger = logging.getLogger(__name__)


def create_metrics_gridplot(
    metrics: Sequence[BaseMetric[GarminResponseEntryDto, Any]],
    period_len: int | None = None,
) -> BytesIO:
    logger.info("Creating metrics gridplot")

    # TODO: Return None if no data
    if period_len:
        metrics = [metric.with_last_n(period_len) for metric in metrics]

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
    logger.info("Creating sleep analysis plot")
    fig = sleep_analysis_plot.plot(sleep, sleep_score, ma_window_size)
    buf = save_plot_to_buffer(fig)
    return buf


# Convert matplotlib figure to bytes
def save_plot_to_buffer(fig: Figure):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf
