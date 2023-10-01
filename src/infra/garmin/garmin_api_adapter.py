import logging
from datetime import date

from src.infra.garmin.dtos.garmin_bb_response import GarminBbResponse
from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_rhr_response import GarminRhrResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.garmin.dtos.garmin_steps_response import GarminStepsResponse
from src.infra.garmin.dtos.garmin_stress_response import GarminStressRespone
from src.infra.garmin.garmin_api_client import GarminApiClient, GarminEndpoint

logger = logging.getLogger(__name__)


# Adapts the GarminApiClient to return DTOs instead of json dict
class GarminApiAdapter:
    def __init__(self, api_client: GarminApiClient) -> None:
        self._api_client = api_client

    def get_daily_rhr(self, start_date: date, end_date: date) -> GarminRhrResponse:
        json_dict = self._api_client.get_data(
            GarminEndpoint.DAILY_RHR, start_date, end_date
        )

        return GarminRhrResponse.from_dict(json_dict)

    def get_daily_steps(self, start_date: date, end_date: date) -> GarminStepsResponse:
        json = self._api_client.get_data(
            GarminEndpoint.DAILY_STEPS, start_date, end_date
        )
        return GarminStepsResponse.from_dict(json)

    def get_daily_stress(self, start_date: date, end_date: date) -> GarminStressRespone:
        json = self._api_client.get_data(
            GarminEndpoint.DAILY_STRESS, start_date, end_date
        )
        return GarminStressRespone.from_dict(json)

    def get_daily_sleep(self, start_date: date, end_date: date) -> GarminSleepResponse:
        json = self._api_client.get_data(
            GarminEndpoint.DAILY_SLEEP, start_date, end_date
        )
        return GarminSleepResponse.from_list(json)

    def get_daily_sleep_score(
        self, start_date: date, end_date: date
    ) -> GarminSleepScoreResponse:
        json = self._api_client.get_data(
            GarminEndpoint.DAILY_SLEEP_SCORE, start_date, end_date
        )
        return GarminSleepScoreResponse.from_list(json)

    def get_daily_hrv(self, start_date: date, end_date: date) -> GarminHrvResponse:
        json = self._api_client.get_data(GarminEndpoint.DAILY_HRV, start_date, end_date)
        return GarminHrvResponse.from_dict(json)

    def get_daily_bb(self, start_date: date, end_date: date) -> GarminBbResponse:
        json = self._api_client.get_data(GarminEndpoint.DAILY_BB, start_date, end_date)
        return GarminBbResponse.from_dict(json)
