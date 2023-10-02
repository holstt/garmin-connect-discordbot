from src.domain.models import HealthSummary
from src.infra.discord.discord_api_client import DiscordApiClient
from src.presentation.discord_messages import (
    DiscordErrorMessage,
    DiscordExceptionMessage,
    DiscordHealthSummaryMessage,
)


# Adapts application requests to discord requests (DTOs)
class DiscordApiAdapter:
    def __init__(
        self,
        discord_client: DiscordApiClient,
    ):
        self.discord_client = discord_client

    # Send health summary to discord webhook
    def send_health_summary(self, healthSummary: HealthSummary) -> None:
        discord_message = DiscordHealthSummaryMessage(healthSummary)
        self.discord_client.send_message(discord_message)

    # Send error message to discord webhook
    def send_error(
        self,
        error_name: str,
        error_message: str,
    ) -> None:
        discord_message = DiscordErrorMessage(error_name, error_message)
        self.discord_client.send_message(discord_message)

    def send_exception(
        self,
        exception: Exception,
        stack_trace: str,
    ) -> None:
        discord_message = DiscordExceptionMessage(exception, stack_trace)
        self.discord_client.send_message(discord_message)
