from io import BytesIO

from src.domain.metrics import HealthSummary, MetricPlot
from src.infra.discord.discord_api_client import DiscordApiClient
from src.presentation.discord_messages import (
    DiscordErrorMessage,
    DiscordExceptionMessage,
    DiscordHealthSummaryMessage,
    MessageFormat,
)
from src.presentation.metric_msg_builder import HealthSummaryViewModel, MetricViewModel
from src.registry import ModelToPresenterConverterRegistry


# Adapts application requests to discord requests (DTOs)
class DiscordApiAdapter:
    def __init__(
        self,
        discord_client: DiscordApiClient,
        message_format: MessageFormat,
        to_vm_registry: ModelToPresenterConverterRegistry,
    ):
        super().__init__()
        self._client = discord_client
        self._message_format = message_format
        self._to_vm_registry = to_vm_registry

    # Send health summary to discord webhook
    def send_health_summary(self, summary: HealthSummary) -> None:
        # Turn into view model
        vms: list[MetricViewModel] = []
        for metric in summary.metrics:
            vm = self._to_vm_registry.convert(metric)
            vms.append(vm)

        summary_vm = HealthSummaryViewModel(
            summary.date,
            vms,
            summary.plots,
        )

        discord_message = DiscordHealthSummaryMessage(summary_vm, self._message_format)
        self._client.send_message(discord_message)

    def send_image(self, image: BytesIO, name: str) -> None:
        self._client.send_image(image, name)

    def send_images(self, plots: list[MetricPlot]) -> None:
        self._client.send_images(
            [plot.data for plot in plots], [f"{plot.id}.png" for plot in plots]
        )

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
