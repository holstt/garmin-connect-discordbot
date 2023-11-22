import logging
from io import BytesIO
from typing import Sequence

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
        super().__init__()
        self._webhook_url = webhook_url

        self._base_client = DiscordWebhook(
            webhook_url,
            rate_limit_retry=True,
            username=service_name,
            avatar_url="https://is2-ssl.mzstatic.com/image/thumb/Purple116/v4/66/ee/6a/66ee6ac7-8c44-0f33-757e-1024b3a7489c/AppIcon-0-1x_U007emarketing-0-6-0-sRGB-85-220.png/256x256bb.jpg",
        )

        self._time_provider = time_provider

    def send_message_str(self, message: str) -> None:
        self._base_client.set_content(message)
        self._base_client.execute()

    def send_message_embed(self, embed: DiscordEmbed) -> None:
        self._base_client.add_embed(embed)
        self._execute()

        # Add time to footer?
        # embed.set_footer(text=f"{self._time_provider.get_current_time()}")

    # XXX: Rate limit on sending multiple images in a row using this method? -> For multi image use send_images
    def send_image(self, image: BytesIO, name: str) -> None:
        self._base_client.add_file(file=image.read(), filename=name)
        self._execute()

    # Attach multiple images to a single message
    def send_images(self, images: Sequence[BytesIO], names: Sequence[str]) -> None:
        for image, name in zip(images, names):
            self._base_client.add_file(file=image.read(), filename=name)
        self._execute()

    # Executes current state of the client and resets it
    def _execute(self) -> None:
        try:
            # base client keeps state -> remove embeds and attachments after sending
            response = self._base_client.execute(remove_embeds=True)
            self._base_client.clear_attachments()
            response.raise_for_status()
        except Exception as e:
            raise DiscordException(f"Error sending message to Discord: {e}") from e

        logger.info(f"Message successfully sent to Discord. Response: {response}")
