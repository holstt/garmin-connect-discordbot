from discord_webhook import DiscordEmbed

from src.domain.health_metrics import HealthSummary
from src.infra.discord_api_client import DiscordApiClient
from src.presentation.discord_messages import (
    DiscordErrorMessage,
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
    def send_summary_message(self, healthSummary: HealthSummary) -> None:
        discord_message = DiscordHealthSummaryMessage(healthSummary)
        self.discord_client.send_message(discord_message)

    # Send exception message to discord webhook
    def send_error_message(
        self,
        error_message: str,
    ) -> None:
        discord_message = DiscordErrorMessage(error_message)
        self.discord_client.send_message(discord_message)
