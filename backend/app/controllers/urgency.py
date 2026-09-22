"""Calendar-day boundaries for the classroom urgency assumption."""
from datetime import datetime
from zoneinfo import ZoneInfo

APPLICATION_TIME_ZONE = ZoneInfo('America/New_York')


def search_day(now: datetime) -> str:
    return now.astimezone(APPLICATION_TIME_ZONE).date().isoformat()


def is_urgent(search_count: int) -> bool:
    return search_count >= 4
