import datetime
from enum import Enum
from typing import NamedTuple, Sequence

import matplotlib.dates as mdates
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from src.infra.garmin.dtos.garmin_stress_response import (
    GarminStressResponse,
    StressEntry,
)

# ALPHA = 0.7  # Transparency for stress bars


class StressColors(Enum):
    REST = "#2A88E6"
    LOW = "#FFB154"
    MEDIUM = "#F27716"
    HIGH = "#DE5809"


class StressSegmentNames(Enum):
    LOW = "Low Stress"
    MEDIUM = "Medium Stress"
    HIGH = "High Stress"
    REST = "Rest Stress"


class StressSegment(NamedTuple):
    name: str
    color: str
    normalized_values: Sequence[float]


class StressPlottingData(NamedTuple):
    dates: Sequence[datetime.date]
    stress_segments: Sequence[StressSegment]


# Tranform into suitable plotting data
# XXX: Gets normalized atm, but should not be necessary if no other plotting on chart
def _transform(stress_dto: GarminStressResponse) -> StressPlottingData:
    def sum_durations(entry: StressEntry):
        valid_durations = [
            entry.values.restStressDuration,
            entry.values.lowStressDuration,
            entry.values.mediumStressDuration,
            entry.values.highStressDuration,
        ]
        return sum([duration for duration in valid_durations if duration])

    max_total_stress = max([sum_durations(entry) for entry in stress_dto.entries])

    dates = [entry.calendarDate for entry in stress_dto.entries]

    high_stress = StressSegment(
        name=StressSegmentNames.HIGH.value,
        color=StressColors.HIGH.value,
        normalized_values=[
            entry.values.highStressDuration / max_total_stress
            if entry.values.highStressDuration
            else 0
            for entry in stress_dto.entries
        ],
    )
    medium_stress = StressSegment(
        name=StressSegmentNames.MEDIUM.value,
        color=StressColors.MEDIUM.value,
        normalized_values=[
            entry.values.mediumStressDuration / max_total_stress
            if entry.values.mediumStressDuration
            else 0
            for entry in stress_dto.entries
        ],
    )
    low_stress = StressSegment(
        name=StressSegmentNames.LOW.value,
        color=StressColors.LOW.value,
        normalized_values=[
            entry.values.lowStressDuration / max_total_stress
            if entry.values.lowStressDuration
            else 0
            for entry in stress_dto.entries
        ],
    )
    rest_stress = StressSegment(
        name=StressSegmentNames.REST.value,
        color=StressColors.REST.value,
        normalized_values=[
            entry.values.restStressDuration / max_total_stress
            if entry.values.restStressDuration
            else 0
            for entry in stress_dto.entries
        ],
    )
    return StressPlottingData(
        dates=dates,
        stress_segments=[rest_stress, low_stress, medium_stress, high_stress],
    )


def plot(
    dto: GarminStressResponse,
):
    plotting_data = _transform(dto)

    # Keep track of current bottom of each bar
    bar_bottoms = [0] * len(plotting_data.dates)

    fig, ax = plt.subplots()
    ax: Axes

    # Iterate each stress segment and plot all bars for that segment
    for segment in plotting_data.stress_segments:
        ax.bar(
            x=plotting_data.dates,  # type: ignore
            height=segment.normalized_values,  # type: ignore
            color=segment.color,
            bottom=bar_bottoms,  # type: ignore
            label=segment.name,
            # alpha=ALPHA,
            # width=bar_width,
        )
        # Add current segment values to the bar buttoms
        bar_bottoms = [sum(x) for x in zip(bar_bottoms, segment.normalized_values)]

    ax.legend()

    ax.set_title(f"Stress Levels")

    fmt = mdates.DateFormatter("%d/%m")
    ax.xaxis.set_major_formatter(fmt)

    return plot
