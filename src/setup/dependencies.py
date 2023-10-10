from typing import NamedTuple, Optional

from garminconnect import Garmin  # type: ignore

from src.application.garmin_service import GarminService
from src.application.scheduler_service import GarminFetchDataScheduler
from src.infra.discord.discord_api_adapter import DiscordApiAdapter
from src.infra.discord.discord_api_client import DiscordApiClient
from src.infra.garmin.garmin_api_adapter import GarminApiAdapter
from src.infra.garmin.garmin_api_client import GarminApiClient
from src.infra.time_provider import TimeProvider
from src.presentation.event_handlers import (ExceptionOccurredEventHandler,
                                             HealthSummaryReadyEventHandler)
from src.setup.config import Config
from src.setup.registry import (DtoToModelConverterRegistry, FetcherRegistry,
                                ResponseToDtoConverterRegistry)
from src.setup.registry_setup import (build_fetcher_registry,
                                      build_plotting_strategies,
                                      build_to_dto_converter_registry,
                                      build_to_model_converter_registry,
                                      build_to_presenter_converter_registry)

# TODO: Use DI framework


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
    fetcher_registry: FetcherRegistry
    to_dto_converter_registry: ResponseToDtoConverterRegistry
    to_model_converter_registry: DtoToModelConverterRegistry


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
    to_vm_converter_registry = build_to_presenter_converter_registry()
    plotting_strategies = build_plotting_strategies()

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
        app_config.message_format,
        to_vm_converter_registry,
        plotting_strategies,
    )

    summary_ready_handler = HealthSummaryReadyEventHandler(discord_api_adapter)

    # Create error handler if needed
    error_handler = None
    if app_config.webhook_error_url:
        discord_error_client = DiscordApiClient(
            app_config.webhook_error_url,
            time_provider,
            service_name="garmin-health-bot",
        )
        # XXX: Error adapter gets unnecessary dependencies
        discord_error_adapter = DiscordApiAdapter(
            discord_error_client,
            app_config.message_format,
            to_vm_converter_registry,
            plotting_strategies,
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
        fetcher_registry,
        to_dto_converter_registry,
        to_model_converter_registry,
    )
