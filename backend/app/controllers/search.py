"""Coordinate submitted searches, history, urgency, and returned prices."""
from datetime import datetime, timezone
from typing import Callable

from app.database import Database, RecordNotFound
from app.controllers.pricing import priced_stay
from app.controllers.urgency import search_day


class SearchController:
    def __init__(self, database: Database, clock: Callable[[], datetime] | None = None):
        self.database = database
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    def submit(self, query: str, user: dict | None) -> list[dict]:
        query = query.strip().casefold()
        stays = self.database.search(query)  # Validate before recording; empty results still count.
        history = {'search_count': 0, 'search_id': None}
        if user:
            now = self.clock()
            history = self.database.record_search(user['user_id'], query,
                                                   now.astimezone(timezone.utc).isoformat(), search_day(now))
        return [priced_stay(stay, **history) for stay in stays]

    def booking_total(self, user_id: str, trip_id: str, search_id: int) -> int:
        history = self.database.saved_search(user_id, search_id)
        for stay in self.database.search(history['query']):
            if stay['trip_id'] == trip_id:
                return priced_stay(stay, history['search_count'])['total_cents']
        raise RecordNotFound('Stay not found in this search.')
