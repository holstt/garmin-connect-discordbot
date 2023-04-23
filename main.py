import logging
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, Optional, Union

import src.config as config
from src import utils
from src.application.garmin_service import GarminService
from src.application.scheduler_service import GarminFetchDataScheduler
from src.infra.discord_api_adapter import DiscordApiAdapter
from src.infra.discord_api_client import DiscordApiClient
from src.infra.garmin_api_client import GarminApiClient, GarminBaseClient
from src.infra.time_provider import TimeProvider
from src.presentation.login_prompt import LoginPrompt
from src.presentation.summary_ready_handler import (
    ExceptionOccurredEventHandler,
    HealthSummaryReadyEventHandler,
)

logger = logging.getLogger(__name__)
discord_api_adapter: Optional[
    DiscordApiAdapter
] = None  # Global access to notify discord on unhandled exceptions


def main() -> None:
    """
    The main function that retrieves environment variables, sets up dependencies, and runs the scheduler.
    """
    (
        email,
        password,
        webhook_url,
        session_path,
        start_update_at_hour,
    ) = config.get_env_variables()
    email, password = get_input_credentials_if_needed(email, password)
    garmin_base_client = authenticate_client(email, password, session_path)
    scheduler = create_scheduler(webhook_url, garmin_base_client, start_update_at_hour)
    scheduler.run()


def get_input_credentials_if_needed(email: Optional[str], password: Optional[str]):
    if not email or not password:
        logger.info("No credentials provided. Prompting for credentials.")
        email, password = LoginPrompt().show()
    return email, password


def authenticate_client(email: str, password: str, session_path: Optional[Path]):
    base_client = GarminBaseClient(
        email,
        password,
        session_file_path=Path(session_path) if session_path else None,
    )
    base_client.login()
    return base_client


# Resolves dependencies and creates scheduler
def create_scheduler(
    webhook_url: str, base_client: GarminBaseClient, start_update_at_hour: int
) -> GarminFetchDataScheduler:
    global discord_api_adapter

    dependencies = resolve_dependencies(webhook_url, base_client, start_update_at_hour)

    return dependencies.scheduler


def resolve_dependencies(
    webhook_url: str, base_client: GarminBaseClient, start_update_at_hour: int
):
    time_provider = TimeProvider()

    garmin_client = GarminApiClient(base_client)
    garmin_service = GarminService(garmin_client)

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
        garmin_service,
        discord_client,
        summary_ready_handler,
        error_handler,
        scheduler,
    )


class Dependencies(NamedTuple):
    time_provider: TimeProvider
    garmin_client: GarminApiClient
    garmin_service: GarminService
    discord_client: DiscordApiClient
    summary_ready_handler: HealthSummaryReadyEventHandler
    error_handler: ExceptionOccurredEventHandler
    scheduler: GarminFetchDataScheduler


def send_exception_to_discord() -> None:
    global discord_api_adapter
    if discord_api_adapter:
        # Get stack trace of exception
        stack_trace = traceback.format_exc()
        discord_api_adapter.send_error(stack_trace)


if __name__ == "__main__":
    try:
        utils.setup_logging()
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        send_exception_to_discord()
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
