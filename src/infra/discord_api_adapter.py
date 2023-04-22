from src.domain.health_metrics import HealthSummary
from src.infra.discord_api_client import DiscordApiClient
from src.presentation.discord_messages import DiscordHealthSummaryMessage


# Adapts health summary (domain object) to discord message (DTO)
class DiscordApiAdapter:
    def __init__(
        self,
        discord_client: DiscordApiClient,
    ):
        self.discord_client = discord_client

    # Send health summary to discord webhook
    def send_summary_message(self, healthSummary: HealthSummary) -> None:
        discord_message = DiscordHealthSummaryMessage(healthSummary)  # Domain -> DTO
        self.discord_client.send_message(discord_message)
