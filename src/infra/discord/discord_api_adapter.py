import logging
from io import BytesIO
from typing import Callable, Sequence

from discord_webhook import DiscordEmbed

from src.domain.metrics import HealthSummary
from src.infra.discord.discord_api_client import DiscordApiClient
from src.presentation.discord_messages import (
    DiscordErrorMessage,
    DiscordExceptionMessage,
)
from src.presentation.view_models import (
    HealthSummaryViewModel,
    MetricPlot,
    MetricViewModel,
)
from src.setup.registry import ModelToVmConverterRegistry, PlottingStrategy

logger = logging.getLogger(__name__)


# Adapts application requests to discord requests (DTOs)
class DiscordApiAdapter:
    def __init__(
        self,
        discord_client: DiscordApiClient,
        message_strategy: Callable[[HealthSummaryViewModel], DiscordEmbed],
        model_to_vm_converter: ModelToVmConverterRegistry,
        plotting_strategies: Sequence[PlottingStrategy],
    ):
        super().__init__()
        self._client = discord_client
        self.message_strategy = message_strategy

        self._model_to_vm_converter = model_to_vm_converter
        self._plotting_strategies = plotting_strategies

    # Send health summary to discord webhook
    def send_health_summary(self, summary: HealthSummary) -> None:
        # Turn into view models
        vms: Sequence[MetricViewModel] = []
        for metric in summary.metrics:
            vm = self._model_to_vm_converter.convert(metric)
            vms.append(vm)

        summary_vm = HealthSummaryViewModel(
            summary.date,
            vms,
        )

        # Create discord message based on injected strategy
        discord_message = self.message_strategy(summary_vm)
        logger.info(f"Sending health summary embed to discord")
        self._client.send_message_embed(discord_message)

        # Create plots for all strategies XXX: If config?
        plots: Sequence[MetricPlot] = []
        for strategy in self._plotting_strategies:
            plot = strategy(summary.metrics)
            if plot:
                plots.append(plot)

        logger.info(f"Sending plots to discord")
        self.send_plots(plots)

    # def send_image(self, image: BytesIO, name: str) -> None:
    #     self._client.send_image(image, name)

    def send_plots(self, plots: Sequence[MetricPlot]) -> None:
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
        self._client.send_message_embed(discord_message)

    def send_exception(
        self,
        exception: Exception,
        stack_trace: str,
    ) -> None:
        discord_message = DiscordExceptionMessage(exception, stack_trace)
        self._client.send_message_embed(discord_message)
