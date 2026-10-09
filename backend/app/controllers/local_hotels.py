"""Local hotel workflow and fixed classroom dates; no provider requests."""
from app.controllers.discovery import distance_meters, RADIUS_METERS
from app.local_hotel_schemas import SaveLocalHotel
from app.saved_hotels import SavedHotelStore


DEMO_DATES = tuple(f'2026-10-{day:02d}' for day in range(10, 15))


class LocalHotelController:
    def __init__(self, store: SavedHotelStore):
        self.store = store

    def save(self, request: SaveLocalHotel) -> dict:
        if distance_meters(request.hotel.latitude, request.hotel.longitude,
                           request.center.model_dump()) > RADIUS_METERS:
            raise ValueError('Hotel must be within 5 km of the searched ZIP location.')
        return self.store.save(request.hotel, request.center, DEMO_DATES)

    def search(self, postcode: str) -> dict:
        return self.store.search(postcode)

    def saved_ids(self, ids: list[str]) -> list[str]:
        return self.store.saved_ids(ids)

    def remove(self, hotel_id: str) -> None:
        self.store.remove(hotel_id)
