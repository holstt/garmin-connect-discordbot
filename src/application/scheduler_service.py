import logging
import random
from datetime import date, datetime, timedelta
from typing import Callable

from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent  # type: ignore
from apscheduler.schedulers.background import BlockingScheduler  # type: ignore

from src.application.garmin_service import GarminService
from src.domain.models import HealthSummary
from src.infra.time_provider import TimeProvider  # type: ignore

logger = logging.getLogger(__name__)


JOB_ID = "garmin_fetch_data"
MIN_WAIT_TIME_MINUTES = 10
MAX_WAIT_TIME_MINUTES = 60


# Schedules data fetching from the garmin api
class GarminFetchDataScheduler:
    def __init__(
        self,
        garmin_service: GarminService,
        time_provider: TimeProvider,
        start_update_at_hour: int,  # TODO: Time type
        summary_ready_event: Callable[[HealthSummary], None],
        exception_event: Callable[[str], None],
    ):
        self._garmin_service = garmin_service
        self._time_provider = time_provider
        self._summary_ready_event = summary_ready_event
        self._start_update_at_hour = start_update_at_hour
        self._scheduler = BlockingScheduler(timezone="UTC")
        self.exception_event = exception_event

        # Add error listener
        self._scheduler.add_listener(self._on_exception, EVENT_JOB_ERROR)

        # At startup, run job immediately
        next_run_time = self._time_provider.get_current_time() + timedelta(seconds=2)

        self._add_job(next_run_time)

    # Add job executing each day at specified time
    def _add_job(self, next_run_time: datetime):
        self._scheduler.add_job(
            self._execute_job_wrapper,
            "cron",
            hour=self._start_update_at_hour,
            next_run_time=next_run_time,
            timezone="UTC",
            name=JOB_ID,
        )

    def _execute_job_wrapper(self) -> None:
        current_date = self._time_provider.get_current_time().date()
        is_success = self._execute_garmin_fetch_task(week_end=current_date)

        # Reschedule job if data was not found
        if not is_success:
            self._reschedule_job()

    # Simply remove and add job again. This will trigger the job at specified delay and then run as scheduled afterwards (unless rescheduled again etc..)
    def _reschedule_job(self):
        # Remove all jobs
        self._scheduler.remove_all_jobs()

        # Now re-add the job but with inital run time set to short delay
        delay = timedelta(
            minutes=(random.randrange(MIN_WAIT_TIME_MINUTES, MAX_WAIT_TIME_MINUTES))
        )

        delay = timedelta(minutes=30)
        next_run_time = self._time_provider.get_current_time() + delay
        logger.info(
            f"Rescheduling job '{JOB_ID}' to run at {next_run_time} (delay: {delay})",
        )
        self._add_job(next_run_time)

    # Alternative: Use reschedule_job to reschedule job to run at specific interval, then reschedule back to its regular schedule at job success
    # def reschedule_garmin_fetch_job(self):
    #     self._scheduler.reschedule_job(
    #         job_id="garmin_fetch_data",
    #         trigger="interval",
    #         minutes=10,
    #     )

    # Returns value determines if job was successful
    def _execute_garmin_fetch_task(self, week_end: date) -> bool:
        logger.info("Started daily garmin fetch job")

        health_summary = self._garmin_service.try_get_weekly_health_summary(
            week_end=week_end
        )

        # Not yet available
        if not health_summary:
            logger.info("Health summary not available yet")
            return False

        # Raise event when summary is available
        self._on_summary_ready(health_summary)
        return True

    def _on_summary_ready(self, healthSummary: HealthSummary):
        self._summary_ready_event(healthSummary)

    def _on_exception(self, event: JobExecutionEvent) -> None:
        if event.exception:
            # Raise exception event
            self.exception_event(event.traceback)  # type: ignore

    def run(self):
        logger.info("Starting scheduler with jobs:")

        self._scheduler.print_jobs()

        self._scheduler.start()
