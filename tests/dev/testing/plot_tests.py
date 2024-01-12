import datetime
import subprocess
from pathlib import Path

from matplotlib import pyplot as plt

from src.domain.metrics import SleepMetrics, SleepScoreMetrics
from src.infra.garmin.dtos import *
from src.infra.plotting import metrics_gridplot
from src.infra.plotting.sleep_analysis_plot import plot as plot_sleep
from src.infra.plotting.stress_plot import plot as plot_stress
from tests.dev.utils.test_utils import load_dto_from_file

##############################################
# DEV TESTING FOR PLOTTING

# Set subdir for saving current test plots
# SUB_DIR = "sleep"
SUB_DIR = "all_metrics"

# LOAD DATA
# Load necessary dtos from saved json files (remember to run json_dump_endpoint.py first)
sleep_dto = load_dto_from_file(GarminSleepResponse)
sleep_score_dto = load_dto_from_file(GarminSleepScoreResponse)

sleep_metric = SleepMetrics(sleep_dto)
sleep_score_metric = SleepScoreMetrics(sleep_score_dto)

# bb_dto = load_dto_from_file(GarminBbResponse)
# rhr_dto = load_dto_from_file(GarminRhrResponse)
# steps_dto = load_dto_from_file(GarminStepsResponse)
# hrv_dto = load_dto_from_file(GarminHrvResponse)

# stress_dto = load_dto_from_file(GarminStressResponse)

# EXECUTE PLOT FUNCTION
# fig = plot_stress(stress_dto)
# fig = plot_sleep(sleep_dto, sleep_score_dto, ma_window_size=7)

fig = plot_sleep(sleep_metric, sleep_score_metric, ma_window_size=7)

# metrics_plot.plot(
#     metrics_plot.MetricsData(
#         sleep_dto,
#         sleep_score_dto,
#         bb_dto,
#         rhr_dto,
#         steps_dto,
#         stress_dto,
#         hrv_dto,
#     ).get_last_n(7)
# )

#############################################

# Save plot to file
plot_dir = Path("../plots").resolve()
save_path = plot_dir.joinpath(
    SUB_DIR, f"{SUB_DIR}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
)
plt.savefig(save_path)
# plt.show()

# open the fig in associated program to view properly (.show will try adapt to screen size)

subprocess.Popen(["start", save_path], shell=True)
