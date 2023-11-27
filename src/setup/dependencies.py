from typing import Callable, NamedTuple, Optional

from garminconnect import Garmin  # type: ignore

from src.application.garmin_service import GarminService
from src.application.scheduler_service import GarminFetchDataScheduler
from src.infra.discord.discord_api_adapter import DiscordApiAdapter
from src.infra.discord.discord_api_client import DiscordApiClient
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.time_provider import TimeProvider
from src.presentation.discord_service import DiscordNotificationService
from src.setup.config import Config
from src.setup.registry_setup import (
    build_fetcher_registry,
    build_message_strategy,
    build_plotting_strategies,
    build_to_dto_converter_registry,
    build_to_model_converter_registry,
    build_to_vm_converter_registry,
)

# TODO: Use DI framework


class Dependencies(NamedTuple):
    time_provider: TimeProvider
    garmin_api_client: GarminApiClient
    garmin_adapter: GarminApiAdapter
    garmin_service: GarminService
    discord_client: DiscordApiClient
    discord_adapter: DiscordApiAdapter
    discord_service: DiscordNotificationService
    scheduler: GarminFetchDataScheduler
    error_handler: Optional[Callable[[Exception, str], None]]


def resolve(app_config: Config) -> Dependencies:
    time_provider = TimeProvider()

    garmin_base_client = Garmin(
        app_config.credentials.email, app_config.credentials.password
    )

    garmin_client = GarminApiClient(
        garmin_base_client, time_provider, app_config.session_file_path
    )
    garmin_adapter = GarminApiAdapter(garmin_client)

    fetcher_registry = build_fetcher_registry(garmin_client)
    to_dto_converter_registry = build_to_dto_converter_registry()
    to_model_converter_registry = build_to_model_converter_registry()
    to_vm_converter_registry = build_to_vm_converter_registry()
    plotting_strategies = build_plotting_strategies()
    message_strategy = build_message_strategy(app_config.message_format)

    garmin_service = GarminService(
        garmin_adapter,
        fetcher_registry,
        to_dto_converter_registry,
        to_model_converter_registry,
        metrics_to_include=app_config.metrics,
    )

    discord_client = DiscordApiClient(
        app_config.webhook_url, time_provider, service_name="garmin-connect-bot"
    )

    discord_api_adapter = DiscordApiAdapter(
        discord_client,
        message_strategy,
        to_vm_converter_registry,
        plotting_strategies,
    )

    discord_service = DiscordNotificationService(discord_api_adapter)

    # Create error handler if needed
    error_handler = None
    if webhook_error_url := app_config.webhook_error_url:
        # TODO: Create simple error notifier

        error_client = DiscordApiClient(
            webhook_error_url, time_provider, service_name="garmin-connect-bot"
        )

        error_adapter = DiscordApiAdapter(
            error_client,
            message_strategy,
            to_vm_converter_registry,
            plotting_strategies,
        )

        error_service = DiscordNotificationService(error_adapter)
        error_handler = error_service.on_exception

    scheduler = GarminFetchDataScheduler(
        garmin_service,
        time_provider,
        summary_ready_event=discord_service.on_summary_ready,
        on_scheduler_exception=error_handler if error_handler else None,
    )
    return Dependencies(
        time_provider,
        garmin_client,
        garmin_adapter,
        garmin_service,
        discord_client,
        discord_api_adapter,
        discord_service,
        scheduler,
        error_handler,
    )
