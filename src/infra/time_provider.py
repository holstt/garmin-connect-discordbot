from datetime import datetime, timezone


class TimeProvider:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
