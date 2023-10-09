import logging

from src.domain.metrics import HealthSummary
from src.infra.discord.discord_api_adapter import DiscordApiAdapter

logger = logging.getLogger(__name__)


class HealthSummaryReadyEventHandler:
    def __init__(self, discord_service: DiscordApiAdapter):
        super().__init__()
        self._service = discord_service

    # When a health summary is ready, send it to discord
    def handle(self, summary: HealthSummary) -> None:
        logger.info(f"Handling event: Health summary ready")
        self._service.send_health_summary(summary)


class ExceptionOccurredEventHandler:
    def __init__(self, discord_service: DiscordApiAdapter):
        super().__init__()

        self.discord_service = discord_service

    # Send exception to discord
    def handle(self, exception: Exception, stack_trace: str) -> None:
        logger.info(f"Handling event: Exception occurred")
        self.discord_service.send_exception(exception, stack_trace)
