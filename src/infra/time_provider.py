from datetime import datetime, timezone


class TimeProvider:
    def get_current_time(self) -> datetime:
        return datetime.now(timezone.utc)
