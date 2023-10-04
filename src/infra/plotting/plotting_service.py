from io import BytesIO

import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import src.infra.plotting.metrics_plot as metrics_plot
import src.infra.plotting.sleep_plot as sleep_plot


def create_metrics_plot(metrics_data: metrics_plot.MetricsData) -> BytesIO:
    fig = metrics_plot.plot(metrics_data)
    buf = save_plot_to_buffer(fig)
    return buf


def create_sleep_plot(
    sleep: metrics_plot.GarminSleepResponse,
    sleep_score: metrics_plot.GarminSleepScoreResponse,
    ma_window_size: int,
) -> BytesIO:
    fig = sleep_plot.plot(sleep, sleep_score, ma_window_size)
    buf = save_plot_to_buffer(fig)
    return buf


def save_plot_to_buffer(fig: Figure):
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)
    return buf
