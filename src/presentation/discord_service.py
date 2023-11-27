import logging

from src.domain.metrics import HealthSummary
from src.infra.discord.discord_api_adapter import ErrorAdapter, HealthSummaryAdapter

logger = logging.getLogger(__name__)

# Notifies discord on events from the application


class HealthSummaryNotificationService:
    def __init__(self, health_summary_adapter: HealthSummaryAdapter):
        super().__init__()
        self._health_summary_adapter = health_summary_adapter

    def on_summary_ready(self, summary: HealthSummary) -> None:
        logger.info(f"Handling event: Health summary ready")
        self._health_summary_adapter.send_health_summary(summary)


class ErrorNotificationService:
    def __init__(self, error_adapter: ErrorAdapter):
        super().__init__()
        self._error_adapter = error_adapter

    def on_exception(self, exception: Exception, stack_trace: str) -> None:
        logger.info(f"Handling event: Exception occurred")
        self._error_adapter.send_exception(exception, stack_trace)
