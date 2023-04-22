import logging

from discord_webhook import DiscordEmbed, DiscordWebhook

from src.infra.time_provider import TimeProvider

logger = logging.getLogger(__name__)


class DiscordException(Exception):
    pass


# Facade/Wraps the discord webhook client
class DiscordApiClient:
    def __init__(
        self,
        webhook_url: str,
        time_provider: TimeProvider,
        service_name: str,  # Username of discord message will be the service name
    ) -> None:
        self._webhook_url = webhook_url
        self._base_client = DiscordWebhook(
            webhook_url, rate_limit_retry=True, username=service_name
        )
        self._time_provider = time_provider

    # Generic method for sending an embedded message to Discord
    def send_message(self, embed: DiscordEmbed) -> None:
        self._base_client.add_embed(embed)

        # Always add time to footer
        embed.set_footer(text=f"{self._time_provider.get_current_time()}")

        try:
            response = self._base_client.execute(remove_embeds=True)
            response.raise_for_status()
        except Exception as e:
            raise DiscordException(f"Error sending message to Discord: {e}") from e

        logger.info(f"Message successfully sent to Discord. Response: {response}")
