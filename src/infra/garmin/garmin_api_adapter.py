import logging
from datetime import date

from src.infra.garmin.dtos.garmin_hrv_response import GarminHrvResponse
from src.infra.garmin.dtos.garmin_sleep_response import GarminSleepResponse
from src.infra.garmin.dtos.garmin_sleep_score_response import GarminSleepScoreResponse
from src.infra.garmin.garmin_api_client import GarminApiClient, GarminEndpoint

logger = logging.getLogger(__name__)


# Adapts the GarminApiClient to return DTOs instead of raw json
class GarminApiAdapter:
    def __init__(self, api_client: GarminApiClient) -> None:
        self._api_client = api_client

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
