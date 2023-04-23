from typing import NamedTuple

from src.application.garmin_service import GarminService
from src.application.scheduler_service import GarminFetchDataScheduler
from src.infra.discord_api_adapter import DiscordApiAdapter
from src.infra.discord_api_client import DiscordApiClient
from src.infra.garmin_api_client import (
    GarminApiAdapter,
    GarminApiClient,
    GarminBaseClient,
)
from src.infra.time_provider import TimeProvider
from src.presentation.summary_ready_handler import (
    ExceptionOccurredEventHandler,
    HealthSummaryReadyEventHandler,
)


class Dependencies(NamedTuple):
    time_provider: TimeProvider
    garmin_client: GarminApiClient
    garmin_adapter: GarminApiAdapter
    garmin_service: GarminService
    discord_client: DiscordApiClient
    discord_adapter: DiscordApiAdapter
    summary_ready_handler: HealthSummaryReadyEventHandler
    error_handler: ExceptionOccurredEventHandler
    scheduler: GarminFetchDataScheduler


def resolve(webhook_url: str, base_client: GarminBaseClient, start_update_at_hour: int):
    time_provider = TimeProvider()

    garmin_client = GarminApiClient(base_client)
    garmin_adapter = GarminApiAdapter(garmin_client)
    garmin_service = GarminService(garmin_adapter)

    discord_client = DiscordApiClient(
        webhook_url, time_provider, service_name="garmin-health-bot"
    )
    discord_api_adapter = DiscordApiAdapter(discord_client)

    summary_ready_handler = HealthSummaryReadyEventHandler(discord_api_adapter)
    error_handler = ExceptionOccurredEventHandler(discord_api_adapter)

    scheduler = GarminFetchDataScheduler(
        garmin_service,
        time_provider,
        start_update_at_hour=start_update_at_hour,
        summary_ready_event=summary_ready_handler.handle,
        exception_event=error_handler.handle,
    )

    return Dependencies(
        time_provider,
        garmin_client,
        garmin_adapter,
        garmin_service,
        discord_client,
        discord_api_adapter,
        summary_ready_handler,
        error_handler,
        scheduler,
    )
