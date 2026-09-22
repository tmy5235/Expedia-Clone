"""Calculate from the stored base rate; round half cents up, never compound."""
from app.controllers.urgency import is_urgent


def priced_stay(stay: dict, search_count: int, search_id: int | None = None) -> dict:
    base = stay['nightly_rate_cents']
    rate = (base * 120 + 50) // 100 if is_urgent(search_count) else base
    return {**stay, 'nightly_rate_cents': rate, 'total_cents': rate * stay['nights'],
            'search_id': search_id, 'search_count': search_count}
