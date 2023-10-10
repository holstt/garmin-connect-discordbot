import logging
import traceback
from datetime import timedelta

import src.setup.config as config
import src.setup.dependencies as dependency_resolver
import src.setup.logging_helper as logging_helper
from src import utils
from src.setup.config import Config

logger = logging.getLogger(__name__)


def main(app_config: Config) -> None:
    """
    Based on the provided env variables, the main function sets up dependencies and runs the scheduler.
    """
    # Get dependencies
    dependencies = dependency_resolver.resolve(app_config)

    try:
        # Ensure we can login to garmin
        garmin_api_client = dependencies.garmin_api_client
        garmin_api_client.login()

        # Add job and start scheduler
        scheduler = dependencies.scheduler
        scheduler.add_garmin_fetch_summary_job(
            app_config.notify_time_of_day, job_name="garmin_weekly_summary_job"
        )
        scheduler.run()
    except Exception as e:
        # Notify discord on exception error if handler configured
        if discord_error_handler := dependencies.error_handler:
            stack_trace = traceback.format_exc()
            discord_error_handler.handle(exception=e, stack_trace=stack_trace)
        raise e  # Re-raise to exit program


from abc import ABC, abstractmethod

if __name__ == "__main__":
    try:
        logging_helper.setup_logging(
            module_logger_name=__name__,
            base_log_level=logging.INFO
            # module_logger_name=__name__, base_log_level=logging.DEBUG
        )
        app_config = config.get_config()
        logging_helper.add_password_filter(app_config.credentials.password)
        main(app_config)
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.exception(
            f"Unhandled exception '{type(e).__name__}' caught in global exception handler: {e}. Program will exit."
        )
        raise e
