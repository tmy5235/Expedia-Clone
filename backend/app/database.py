"""SQLite storage and one-time import of the fictional classroom records."""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
import sqlite3
from typing import Iterator
from uuid import uuid4

from app.hotel_search import DATA_DIRECTORY, _read_csv


class RecordNotFound(ValueError):
    pass


STAY_SELECT = """
    SELECT t.trip_id, t.trip_name, h.hotel_id, h.hotel_name, h.city, h.state,
           t.check_in, t.check_out,
           CAST(julianday(t.check_out) - julianday(t.check_in) AS INTEGER) AS nights,
           h.nightly_rate_cents,
           CAST(julianday(t.check_out) - julianday(t.check_in) AS INTEGER)
               * h.nightly_rate_cents AS total_cents
    FROM trips t JOIN hotels h ON h.hotel_id = t.hotel_id
"""
BOOKING_SELECT = """
    SELECT b.*, u.display_name, t.trip_name, t.check_in, t.check_out, h.hotel_name,
           CAST(julianday(t.check_out) - julianday(t.check_in) AS INTEGER)
               * h.nightly_rate_cents AS total_cents
    FROM bookings b JOIN users u ON u.user_id = b.user_id
    JOIN trips t ON t.trip_id = b.trip_id JOIN hotels h ON h.hotel_id = t.hotel_id
"""


class Database:
    def __init__(self, path: Path, data_directory: Path = DATA_DIRECTORY):
        self.path = path
        self.data_directory = data_directory

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            # Lock before checking the marker so simultaneous starts cannot seed twice.
            db.execute("BEGIN IMMEDIATE")
            if db.execute("PRAGMA user_version").fetchone()[0] == 1:
                return
            for statement in (
                """CREATE TABLE hotels (
                    hotel_id TEXT PRIMARY KEY, hotel_name TEXT NOT NULL,
                    city TEXT NOT NULL, state TEXT NOT NULL,
                    nightly_rate_cents INTEGER NOT NULL CHECK(nightly_rate_cents >= 0))""",
                """CREATE TABLE trips (
                    trip_id TEXT PRIMARY KEY, hotel_id TEXT NOT NULL REFERENCES hotels(hotel_id),
                    trip_name TEXT NOT NULL, check_in TEXT NOT NULL, check_out TEXT NOT NULL,
                    CHECK(julianday(check_out) > julianday(check_in)))""",
                "CREATE TABLE users (user_id TEXT PRIMARY KEY, display_name TEXT NOT NULL)",
                """CREATE TABLE bookings (
                    booking_id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES users(user_id),
                    trip_id TEXT NOT NULL REFERENCES trips(trip_id), booked_on TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('confirmed', 'cancelled')))""",
            ):
                db.execute(statement)
            hotels = _read_csv(self.data_directory / "hotels.csv",
                               {"hotel_id", "hotel_name", "city", "state", "nightly_rate_usd"})
            db.executemany("INSERT INTO hotels VALUES (?, ?, ?, ?, ?)", [
                (h["hotel_id"], h["hotel_name"], h["city"], h["state"],
                 int(Decimal(h["nightly_rate_usd"]) * 100)) for h in hotels
            ])
            for table, columns in (
                ("trips", ("trip_id", "hotel_id", "trip_name", "check_in", "check_out")),
                ("users", ("user_id", "display_name")),
                ("bookings", ("booking_id", "user_id", "trip_id", "booked_on", "status")),
            ):
                rows = _read_csv(self.data_directory / f"{table}.csv", set(columns))
                placeholders = ", ".join("?" for _ in columns)
                # Table and column names above are fixed application constants.
                db.executemany(f"INSERT INTO {table} VALUES ({placeholders})",
                               [tuple(row[column] for column in columns) for row in rows])
            db.execute("PRAGMA user_version = 1")

    def search(self, hotel_name: str) -> list[dict]:
        query = hotel_name.strip()
        if not query:
            raise ValueError("Enter a hotel name.")
        with self.connect() as db:
            db.create_function("casefold", 1, str.casefold)
            return [dict(row) for row in db.execute(
                STAY_SELECT + " WHERE instr(casefold(h.hotel_name), ?) > 0 ORDER BY h.hotel_name, t.trip_id",
                (query.casefold(),),
            )]

    def users(self) -> list[dict]:
        with self.connect() as db:
            return [dict(row) for row in db.execute("SELECT * FROM users ORDER BY user_id")]

    @staticmethod
    def require_user(db: sqlite3.Connection, user_id: str) -> None:
        if db.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,)).fetchone() is None:
            raise RecordNotFound("Traveler not found.")

    def history(self, user_id: str) -> list[dict]:
        with self.connect() as db:
            self.require_user(db, user_id)
            return [dict(row) for row in db.execute(
                BOOKING_SELECT + " WHERE b.user_id = ? ORDER BY b.booked_on DESC, b.booking_id DESC",
                (user_id,),
            )]

    def create_booking(self, user_id: str, trip_id: str) -> dict:
        with self.connect() as db:
            self.require_user(db, user_id)
            if db.execute("SELECT 1 FROM trips WHERE trip_id = ?", (trip_id,)).fetchone() is None:
                raise RecordNotFound("Stay not found.")
            booking_id = f"B-{uuid4().hex}"
            db.execute("INSERT INTO bookings VALUES (?, ?, ?, ?, 'confirmed')",
                       (booking_id, user_id, trip_id, date.today().isoformat()))
            booking = dict(db.execute(BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,)).fetchone())
        return booking

    def cancel_booking(self, booking_id: str, user_id: str) -> dict:
        with self.connect() as db:
            result = db.execute(
                "UPDATE bookings SET status = 'cancelled' WHERE booking_id = ? AND user_id = ?",
                (booking_id, user_id),
            )
            if result.rowcount != 1:
                raise RecordNotFound("Booking not found for this traveler.")
            booking = dict(db.execute(BOOKING_SELECT + " WHERE b.booking_id = ?", (booking_id,)).fetchone())
        return booking

    def delete_booking(self, booking_id: str, user_id: str) -> None:
        with self.connect() as db:
            result = db.execute("DELETE FROM bookings WHERE booking_id = ? AND user_id = ?",
                                (booking_id, user_id))
            if result.rowcount != 1:
                raise RecordNotFound("Booking not found for this traveler.")
