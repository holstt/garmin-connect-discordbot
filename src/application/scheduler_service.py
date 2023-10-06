import logging
import random
from datetime import date, datetime, time, timedelta
from typing import Callable, Optional

from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent  # type: ignore
from apscheduler.job import Job  # type: ignore
from apscheduler.schedulers.background import BlockingScheduler  # type: ignore
from apscheduler.triggers.cron import CronTrigger  # type: ignore

from src.application.garmin_service import GarminService
from src.domain.metrics import HealthSummary
from src.infra.time_provider import TimeProvider  # type: ignore

logger = logging.getLogger(__name__)


MIN_WAIT_TIME_MINUTES = 30
MAX_WAIT_TIME_MINUTES = 60


class GarminSchedulerError(Exception):
    pass


# Schedules data fetching from the garmin api
class GarminFetchDataScheduler:
    def __init__(
        self,
        garmin_service: GarminService,
        time_provider: TimeProvider,
        summary_ready_event: Callable[[HealthSummary], None],
        exception_event: Optional[Callable[[Exception, str], None]],
    ):
        super().__init__()
        self._garmin_service = garmin_service
        self._time_provider = time_provider
        self._summary_ready_event = summary_ready_event
        self._scheduler = BlockingScheduler(timezone="UTC")
        self.exception_event = exception_event

        # Add error listener
        self._scheduler.add_listener(self._on_exception, EVENT_JOB_ERROR)

    # Add job executing each day at specified time
    def add_garmin_fetch_summary_job(
        self,
        fetch_start_time: time,
        job_name: str,
    ):
        # Check if job should be run immediately
        current_time = (
            self._time_provider.now()
        )  # FIX: not using time zone speficied by user

        if fetch_start_time <= current_time.time():
            logger.info(
                f"Current time '{current_time.time()}' has passed notify time {fetch_start_time}, running job immediately"
            )
            # Run immediately if we have passed the start time
            next_run_time = current_time + timedelta(
                seconds=2
            )  # Small delay to allow scheduler to start
        else:
            logger.info(
                f"Current '{current_time.time()}' has not passed notify time {fetch_start_time} yet, scheduling job as normal"
            )
            next_run_time = None

        self._add_garmin_fetch_summary_job(
            fetch_start_time=fetch_start_time,
            job_name=job_name,
            next_run_time=next_run_time,
        )

    def _add_garmin_fetch_summary_job(
        self,
        fetch_start_time: time,
        job_name: str,
        next_run_time: Optional[datetime],
    ):
        job = self._scheduler.add_job(
            self._execute_job_wrapper,
            "cron",
            hour=fetch_start_time.hour,
            minute=fetch_start_time.minute,
            second=fetch_start_time.second,
            timezone="UTC",
            name=job_name,
            id=job_name,
            args=[job_name, fetch_start_time],
        )
        if next_run_time:
            job.modify(next_run_time=next_run_time)

    def _execute_job_wrapper(self, job_id: str, fetch_start_time: time) -> None:
        current_date = self._time_provider.now().date()
        is_success = self._execute_garmin_fetch_task(week_end=current_date)

        # Reschedule job if data was not found
        if not is_success:
            delay_until_retry = timedelta(
                minutes=(random.randrange(MIN_WAIT_TIME_MINUTES, MAX_WAIT_TIME_MINUTES))
            )
            self._reschedule_job(fetch_start_time, job_id, delay_until_retry)

    # Returns value determines if job was successful
    def _execute_garmin_fetch_task(self, week_end: date) -> bool:
        logger.info("Started daily garmin fetch job")

        health_summary = self._garmin_service.try_get_weekly_health_summary(
            week_end=week_end
        )

        # Handle summary not yet available
        if not health_summary:
            logger.info("Health summary not available yet")
            return False

        # Raise event when summary is available
        self._on_summary_ready(health_summary)
        return True

    # Simply modify the next run time of the job. This will trigger the job at specified delay and then run as scheduled afterwards (unless rescheduled again etc..)
    def _reschedule_job(self, fetch_start_time: time, job_id: str, delay: timedelta):
        next_run_time = self._time_provider.now() + delay
        logger.info(
            f"Rescheduling (modifying next_run_time) job '{job_id}' to run at {next_run_time} (delay: {delay})",
        )

        job: Job = self._scheduler.get_job(job_id)  # type: ignore
        if not job:
            raise GarminSchedulerError(f"Rescheduling error: '{job_id}' not found")

        job.modify(next_run_time=next_run_time)

    def _on_summary_ready(self, healthSummary: HealthSummary):
        self._summary_ready_event(healthSummary)

    def _on_exception(self, event: JobExecutionEvent) -> None:
        if event.exception and self.exception_event:
            # Raise exception event
            self.exception_event(event.exception, event.traceback)  # type: ignore

    def run(self):
        logger.info("Starting scheduler with jobs:")

        self._scheduler.print_jobs()

        self._scheduler.start()
