import logging

from src.domain.metrics import HealthSummary
from src.infra.discord.discord_api_adapter import DiscordApiAdapter

logger = logging.getLogger(__name__)


# Gets notified by infra layer when a new health summary is ready
class DiscordNotificationService:
    def __init__(self, adapter: DiscordApiAdapter):
        super().__init__()
        self._adapter = adapter

    # When a health summary is ready, send it to discord
    def on_summary_ready(self, summary: HealthSummary) -> None:
        logger.info(f"Handling event: Health summary ready")
        self._adapter.send_health_summary(summary)

    # Send exception to discord
    def on_exception(self, exception: Exception, stack_trace: str) -> None:
        logger.info(f"Handling event: Exception occurred")
        self._adapter.send_exception(exception, stack_trace)
