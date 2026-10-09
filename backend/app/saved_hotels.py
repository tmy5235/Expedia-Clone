"""Model operations for local hotels; every mutation commits atomically."""
import sqlite3

from app.database import Database
from app.local_hotel_schemas import LocalCenter, LocalPlace


HOTEL_SELECT = 'SELECT hotel_id AS place_id, name, address, latitude, longitude FROM saved_hotels'


class SavedHotelStore:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def with_nights(db: sqlite3.Connection, row: sqlite3.Row) -> dict:
        return {**dict(row), 'demo_nights': [dict(night) for night in db.execute(
            'SELECT stay_date, nightly_rate_cents, rooms_available FROM demo_hotel_nights '
            'WHERE hotel_id = ? ORDER BY stay_date', (row['place_id'],))]}

    def save(self, hotel: LocalPlace, center: LocalCenter, days: tuple[str, ...]) -> dict:
        with self.database.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('''INSERT INTO saved_hotels (hotel_id, name, address, latitude, longitude)
                VALUES (?, ?, ?, ?, ?) ON CONFLICT(hotel_id) DO NOTHING''',
                (hotel.place_id, hotel.name, hotel.address, hotel.latitude, hotel.longitude))
            db.execute('''INSERT INTO saved_search_locations
                (postcode, country_code, locality, latitude, longitude) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(postcode) DO NOTHING''',
                (center.postcode, center.country_code, center.locality, center.latitude, center.longitude))
            db.execute('''INSERT INTO saved_hotel_zips (hotel_id, postcode) VALUES (?, ?)
                ON CONFLICT(hotel_id, postcode) DO NOTHING''', (hotel.place_id, center.postcode))
            # Omit rate/rooms to use the schema's explicitly fictional defaults.
            db.executemany('''INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)
                ON CONFLICT(hotel_id, stay_date) DO NOTHING''', ((hotel.place_id, day) for day in days))
            result = self.with_nights(db, db.execute(HOTEL_SELECT + ' WHERE hotel_id = ?',
                                                   (hotel.place_id,)).fetchone())
        return result

    def search(self, postcode: str) -> dict:
        with self.database.connect() as db:
            db.execute('BEGIN')  # One consistent snapshot for hotels, context and nightly data.
            rows = db.execute(HOTEL_SELECT + ''' WHERE hotel_id IN (
                SELECT hotel_id FROM saved_hotel_zips WHERE postcode = ?) ORDER BY hotel_id''',
                (postcode,)).fetchall()
            center = db.execute('SELECT * FROM saved_search_locations WHERE postcode = ?',
                                (postcode,)).fetchone()
            return {'center': dict(center) if rows and center else None,
                    'hotels': [self.with_nights(db, row) for row in rows]}

    def saved_ids(self, ids: list[str]) -> list[str]:
        if not ids:
            return []
        with self.database.connect() as db:
            placeholders = ','.join('?' for _ in ids)
            return [row[0] for row in db.execute(
                f'SELECT hotel_id FROM saved_hotels WHERE hotel_id IN ({placeholders}) ORDER BY hotel_id', ids)]

    def remove(self, hotel_id: str) -> None:
        with self.database.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            postcodes = [row[0] for row in db.execute(
                'SELECT postcode FROM saved_hotel_zips WHERE hotel_id = ?', (hotel_id,))]
            db.execute('DELETE FROM demo_hotel_nights WHERE hotel_id = ?', (hotel_id,))
            db.execute('DELETE FROM saved_hotel_zips WHERE hotel_id = ?', (hotel_id,))
            db.execute('DELETE FROM saved_hotels WHERE hotel_id = ?', (hotel_id,))
            for postcode in postcodes:
                db.execute('''DELETE FROM saved_search_locations WHERE postcode = ?
                    AND NOT EXISTS (SELECT 1 FROM saved_hotel_zips WHERE postcode = ?)''', (postcode, postcode))
