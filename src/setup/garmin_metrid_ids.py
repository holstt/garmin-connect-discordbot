from enum import Enum


# Unique identifier for each Garmin metric.
# Order determines: the order in which metrics are fetched and the order which metrics are displayed
# NB: Metrics obtained while sleeping most likely to be missing in today's data (e.g. if no sleep registered yet, or if not wearing device during sleep). Should be requested first to avoid unnecessary requests
class GarminMetricId(Enum):
    SLEEP = "sleep"
    SLEEP_SCORE = "sleep_score"
    RHR = "rhr"
    HRV = "hrv"
    BB = "bb"
    STRESS = "stress"
    # STEPS = "steps"
