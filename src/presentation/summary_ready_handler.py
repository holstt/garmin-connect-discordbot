import logging

from src.domain.health_metrics import HealthSummary
from src.infra.discord_api_adapter import DiscordApiAdapter

logger = logging.getLogger(__name__)


class HealthSummaryReadyEventHandler:
    def __init__(self, discord_service: DiscordApiAdapter):
        self.discord_service = discord_service

    # When a health summary is ready, send it to discord
    def handle(self, summary: HealthSummary) -> None:
        logger.info(f"Handling event: Health summary ready")
        self.discord_service.send_summary_message(summary)
