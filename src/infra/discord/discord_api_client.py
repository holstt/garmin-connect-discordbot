import logging
from io import BytesIO
from typing import Optional

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
            webhook_url,
            rate_limit_retry=True,
            username=service_name,
            avatar_url="https://is2-ssl.mzstatic.com/image/thumb/Purple116/v4/66/ee/6a/66ee6ac7-8c44-0f33-757e-1024b3a7489c/AppIcon-0-1x_U007emarketing-0-6-0-sRGB-85-220.png/256x256bb.jpg",
        )

        self._time_provider = time_provider

    # Generic method for sending an embedded message to Discord
    def send_message(self, embed: DiscordEmbed) -> None:
        self._base_client.add_embed(embed)

        # Always add time to footer
        # embed.set_footer(text=f"{self._time_provider.get_current_time()}")

        try:
            response = self._base_client.execute(remove_embeds=True)
            response.raise_for_status()
        except Exception as e:
            raise DiscordException(f"Error sending message to Discord: {e}") from e

        logger.info(f"Message successfully sent to Discord. Response: {response}")

    # XXX: Rate limit on sending multiple images in a row using this method? -> For multi image use send_images
    def send_image(self, image: BytesIO, name: str) -> None:
        self._base_client.add_file(file=image.read(), filename=name)

        try:
            response = self._base_client.execute()
            response.raise_for_status()
        except Exception as e:
            raise DiscordException(f"Error sending image to Discord: {e}") from e

        logger.info(f"Image successfully sent to Discord. Response: {response}")

    # Attach multiple images to a single message
    def send_images(self, images: list[BytesIO], names: list[str]) -> None:
        for image, name in zip(images, names):
            self._base_client.add_file(file=image.read(), filename=name)

        try:
            response = self._base_client.execute()
            response.raise_for_status()
        except Exception as e:
            raise DiscordException(f"Error sending images to Discord: {e}") from e

        logger.info(f"Images successfully sent to Discord. Response: {response}")
