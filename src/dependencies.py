from typing import NamedTuple, Optional

from garminconnect import Garmin  # type: ignore

from src.application.garmin_service import GarminService
from src.application.scheduler_service import GarminFetchDataScheduler
from src.config import Config
from src.infra.discord.discord_api_adapter import DiscordApiAdapter
from src.infra.discord.discord_api_client import DiscordApiClient
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.time_provider import TimeProvider
from src.presentation.event_handlers import (
    ExceptionOccurredEventHandler,
    HealthSummaryReadyEventHandler,
)


class Dependencies(NamedTuple):
    time_provider: TimeProvider
    garmin_api_client: GarminApiClient
    garmin_adapter: GarminApiAdapter
    garmin_service: GarminService
    discord_client: DiscordApiClient
    discord_adapter: DiscordApiAdapter
    summary_ready_handler: HealthSummaryReadyEventHandler
    scheduler: GarminFetchDataScheduler
    error_handler: Optional[ExceptionOccurredEventHandler]


def resolve(app_config: Config) -> Dependencies:
    time_provider = TimeProvider()

    garmin_base_client = Garmin(
        app_config.credentials.email, app_config.credentials.password
    )

    garmin_client = GarminApiClient(
        garmin_base_client, time_provider, app_config.session_file_path
    )
    garmin_adapter = GarminApiAdapter(garmin_client)
    garmin_service = GarminService(garmin_adapter)

    discord_client = DiscordApiClient(
        app_config.webhook_url, time_provider, service_name="garmin-connect-bot"
    )

    discord_api_adapter = DiscordApiAdapter(discord_client, app_config.message_format)

    summary_ready_handler = HealthSummaryReadyEventHandler(discord_api_adapter)

    # Create error handler if needed
    error_handler = None
    if app_config.webhook_error_url:
        discord_error_client = DiscordApiClient(
            app_config.webhook_error_url,
            time_provider,
            service_name="garmin-health-bot",
        )
        discord_error_adapter = DiscordApiAdapter(
            discord_error_client, app_config.message_format
        )
        error_handler = ExceptionOccurredEventHandler(discord_error_adapter)

    scheduler = GarminFetchDataScheduler(
        garmin_service,
        time_provider,
        summary_ready_event=summary_ready_handler.handle,
        exception_event=error_handler.handle if error_handler else None,
    )
    return Dependencies(
        time_provider,
        garmin_client,
        garmin_adapter,
        garmin_service,
        discord_client,
        discord_api_adapter,
        summary_ready_handler,
        scheduler,
        error_handler,
    )
