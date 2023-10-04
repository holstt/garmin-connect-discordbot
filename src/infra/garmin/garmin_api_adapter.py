import logging
from datetime import date
from typing import Any, Optional

from src.domain.common import DatePeriod
from src.infra.garmin.dtos.garmin_bb_response import GarminBbResponse
from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_rhr_response import GarminRhrResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.garmin.dtos.garmin_steps_response import GarminStepsResponse
from src.infra.garmin.dtos.garmin_stress_response import GarminDto, GarminStressResponse
from src.infra.garmin.garmin_api_client import GarminApiClient, GarminEndpoint

logger = logging.getLogger(__name__)


dto_to_endpoint = {
    GarminRhrResponse: GarminEndpoint.DAILY_RHR,
    GarminStepsResponse: GarminEndpoint.DAILY_STEPS,
    GarminStressResponse: GarminEndpoint.DAILY_STRESS,
    GarminSleepResponse: GarminEndpoint.DAILY_SLEEP,
    GarminSleepScoreResponse: GarminEndpoint.DAILY_SLEEP_SCORE,
    GarminHrvResponse: GarminEndpoint.DAILY_HRV,
    GarminBbResponse: GarminEndpoint.DAILY_BB,
}


# Adapts the GarminApiClient to return DTOs instead of json dict
class GarminApiAdapter:
    def __init__(self, api_client: GarminApiClient) -> None:
        self._api_client = api_client

    def get_daily_rhr(self, period: DatePeriod) -> Optional[GarminRhrResponse]:
        json = self._api_client.get_data(GarminEndpoint.DAILY_RHR, period)
        return GarminRhrResponse.from_json(json) if json else None

    def get_daily_steps(self, period: DatePeriod) -> Optional[GarminStepsResponse]:
        json = self._api_client.get_data(GarminEndpoint.DAILY_STEPS, period)
        return GarminStepsResponse.from_json(json) if json else None

    def get_daily_stress(self, period: DatePeriod) -> Optional[GarminStressResponse]:
        json = self._api_client.get_data(dto_to_endpoint[GarminStressResponse], period)
        return GarminStressResponse.from_json(json) if json else None

    def get_daily_sleep(self, period: DatePeriod) -> Optional[GarminSleepResponse]:
        json = self._api_client.get_data(GarminEndpoint.DAILY_SLEEP, period)
        return GarminSleepResponse.from_json(json) if json else None

    def get_daily_sleep_score(
        self, period: DatePeriod
    ) -> Optional[GarminSleepScoreResponse]:
        json = self._api_client.get_data(GarminEndpoint.DAILY_SLEEP_SCORE, period)
        return GarminSleepScoreResponse.from_json(json) if json else None

    def get_daily_hrv(self, period: DatePeriod) -> Optional[GarminHrvResponse]:
        json = self._api_client.get_data(GarminEndpoint.DAILY_HRV, period)
        return GarminHrvResponse.from_json(json) if json else None

    def get_daily_bb(self, period: DatePeriod) -> Optional[GarminBbResponse]:
        json = self._api_client.get_data(GarminEndpoint.DAILY_BB, period)
        return GarminBbResponse.from_json(json) if json else None
