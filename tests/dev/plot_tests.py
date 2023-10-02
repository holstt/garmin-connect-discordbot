import datetime
from pathlib import Path

from matplotlib import pyplot as plt

from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.plotting.sleep_plot import plot as plot_sleep
from tests.dev.test_utils import load_dto_from_file

# stress_dto = load_dto_from_disk(GarminStressResponse)
sleep_dto = load_dto_from_file(GarminSleepResponse)
sleep_score_dto = load_dto_from_file(GarminSleepScoreResponse)
#############################################

# Get dates for from one of the dtos (they should be the same)
dates = [entry.calendarDate for entry in sleep_dto.entries]

fig = plot_sleep(sleep_dto, sleep_score_dto, ma_window_size=7)

# Save plot to file
save_path = Path(
    f"../plots/sleep_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
)
plt.savefig(save_path)

plt.show()
