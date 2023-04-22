import logging
from pathlib import Path
from typing import Optional

import src.config as config
from src import utils
from src.application.garmin_service import GarminService
from src.application.scheduler_service import GarminFetchDataScheduler
from src.infra.discord_api_adapter import DiscordApiAdapter
from src.infra.discord_api_client import DiscordApiClient
from src.infra.garmin_api_client import GarminApiClient, GarminBaseClient
from src.infra.time_provider import TimeProvider
from src.presentation.login_prompt import LoginPrompt
from src.presentation.summary_ready_handler import HealthSummaryReadyEventHandler

logger = logging.getLogger(__name__)


def main() -> None:
    """
    The main function that retrieves environment variables, sets up dependencies, and runs the scheduler.
    """
    email, password, webhook_url, session_path, start_update_at_hour = config.get_env()
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
    time_provider = TimeProvider()

    garmin_client = GarminApiClient(base_client)
    garmin_service = GarminService(garmin_client)

    discord_client = DiscordApiClient(
        webhook_url, time_provider, service_name="garmin-health-bot"
    )
    discord_service = DiscordApiAdapter(discord_client)

    event_handler = HealthSummaryReadyEventHandler(discord_service)

    scheduler = GarminFetchDataScheduler(
        garmin_service,
        time_provider,
        summary_ready_event=event_handler.handle,
        start_update_at_hour=start_update_at_hour,
    )

    return scheduler


if __name__ == "__main__":
    try:
        utils.setup_logging()
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.exception(f"Unhandled exception occurred: {e}")
        raise e
