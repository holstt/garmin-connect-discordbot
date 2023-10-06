from io import BytesIO

from src.domain.metrics import HealthSummary
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
        super().__init__()
        self._client = discord_client

    # Send health summary to discord webhook
    def send_health_summary(self, healthSummary: HealthSummary) -> None:
        discord_message = DiscordHealthSummaryMessage(healthSummary)
        self._client.send_message(discord_message)

    def send_image(self, image: BytesIO, name: str) -> None:
        self._client.send_image(image, name)

    def send_images(self, images: list[BytesIO], names: list[str]) -> None:
        self._client.send_images(images, names)

    # Send error message to discord webhook
    def send_error(
        self,
        error_name: str,
        error_message: str,
    ) -> None:
        discord_message = DiscordErrorMessage(error_name, error_message)
        self._client.send_message(discord_message)

    def send_exception(
        self,
        exception: Exception,
        stack_trace: str,
    ) -> None:
        discord_message = DiscordExceptionMessage(exception, stack_trace)
        self._client.send_message(discord_message)
