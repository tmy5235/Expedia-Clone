"""Schema-only Part 2 checks. Every database is temporary; no provider calls."""
from pathlib import Path
import sqlite3

import pytest

from app.database import Database


LEGACY_TABLES = ('hotels', 'trips', 'users', 'bookings', 'sessions', 'search_history')
HOTEL_INSERT = '''INSERT INTO saved_hotels
    (hotel_id, name, address, latitude, longitude) VALUES (?, ?, ?, ?, ?)'''


@pytest.fixture
def database(tmp_path: Path) -> Database:
    database = Database(tmp_path / 'schema.sqlite3')
    database.initialize()
    return database


def legacy_snapshot(database: Database) -> dict:
    with database.connect() as db:
        return {
            'schema': [tuple(row) for row in db.execute(
                "SELECT type, name, sql FROM sqlite_master "
                "WHERE tbl_name IN ('hotels','trips','users','bookings','sessions','search_history') "
                "ORDER BY type, name")],
            'rows': {table: [tuple(row) for row in db.execute(
                f'SELECT * FROM {table} ORDER BY rowid')] for table in LEGACY_TABLES},
        }


def downgrade_fixture_to_v2(database: Database) -> None:
    """The six original table definitions are unchanged by version 3."""
    with database.connect() as db:
        db.execute('DROP TABLE saved_hotel_zips')
        db.execute('DROP TABLE saved_search_locations')
        db.execute('DROP TABLE demo_hotel_nights')
        db.execute('DROP TABLE saved_hotels')
        db.execute('PRAGMA user_version = 2')


def test_fresh_database_and_exact_provider_id_mapping(database: Database) -> None:
    # Preserve case, leading zeros, punctuation and whitespace, with no ID rewrite.
    api_hotel = {'place_id': ' 00AbC/Place:001 ', 'name': None, 'address': None,
                 'latitude': 40.801, 'longitude': -73.041}
    with database.connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 5
        assert db.execute('PRAGMA foreign_keys').fetchone()[0] == 1
        assert db.execute('SELECT count(*) FROM saved_hotels').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM demo_hotel_nights').fetchone()[0] == 0
        db.execute(HOTEL_INSERT, (api_hotel['place_id'], api_hotel['name'],
                   api_hotel['address'], api_hotel['latitude'], api_hotel['longitude']))
        assert dict(db.execute('SELECT * FROM saved_hotels').fetchone()) == {
            'hotel_id': api_hotel['place_id'], **{k: v for k, v in api_hotel.items() if k != 'place_id'}}
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(HOTEL_INSERT, (api_hotel['place_id'], 'Duplicate', None, 0, 0))
        db.execute(HOTEL_INSERT, (api_hotel['place_id'].lower(), 'Distinct ID', None, 0, 0))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(HOTEL_INSERT, (None, None, None, 0, 0))


def test_v2_migration_preserves_all_records_and_restarts(database: Database, tmp_path: Path) -> None:
    downgrade_fixture_to_v2(database)
    user = database.create_account('fictional_migration_user', 'fictional-demo')
    database.save_session('fictional-session', user['user_id'], None)
    database.record_search(user['user_id'], 'valley', '2026-10-01T12:00:00Z', '2026-10-01')
    booking = database.create_booking(user['user_id'], 'T001', 45678)
    database.cancel_booking(booking['booking_id'], user['user_id'])
    database.delete_booking('B001', 'U001')
    before = legacy_snapshot(database)
    # Missing CSV directory ensures an existing database is never reseeded.
    restarted = Database(database.path, tmp_path / 'no-seed-files')
    restarted.initialize()
    assert legacy_snapshot(restarted) == before
    with restarted.connect() as db:
        db.execute(HOTEL_INSERT, ('Provider:001', None, None, -90, 180))
        db.execute("INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES ('Provider:001', '2026-10-01')")
        db.execute("UPDATE demo_hotel_nights SET nightly_rate_cents=12345, rooms_available=7")
    for _ in range(2):
        Database(database.path, tmp_path / 'no-seed-files').initialize()
    assert legacy_snapshot(restarted) == before
    with restarted.connect() as db:
        assert tuple(db.execute('SELECT * FROM demo_hotel_nights').fetchone()) == (
            'Provider:001', '2026-10-01', 12345, 7)
        assert db.execute('PRAGMA user_version').fetchone()[0] == 5
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('latitude,longitude', [
    (None, 0), (0, None), (90.01, 0), (-90.01, 0), (0, 180.01), (0, -180.01),
    ('invalid', 0), (0, 'invalid'), (float('inf'), 0), (0, float('-inf')), (float('nan'), 0),
])
def test_invalid_coordinates_rejected(database: Database, latitude, longitude) -> None:
    with database.connect() as db, pytest.raises(sqlite3.IntegrityError):
        db.execute(HOTEL_INSERT, ('bad', None, None, latitude, longitude))


def test_night_defaults_uniqueness_foreign_keys_and_date_boundaries(database: Database) -> None:
    with database.connect() as db:
        for hotel_id, lat, lon in [('one', -90, -180), ('two', 90, 180)]:
            db.execute(HOTEL_INSERT, (hotel_id, None, None, lat, lon))
        for hotel_id, day in [('one', '2026-10-01'), ('one', '2026-10-02'),
                              ('two', '2026-10-01'), ('one', '2028-02-29'),
                              ('one', '0001-01-01'), ('one', '9999-12-31')]:
            db.execute('INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)', (hotel_id, day))
        assert all(tuple(row) == (10000, 20) for row in db.execute(
            'SELECT nightly_rate_cents, rooms_available FROM demo_hotel_nights'))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES ('one', '2026-10-01')")
        for hotel_id in ('missing', None):
            with pytest.raises(sqlite3.IntegrityError):
                db.execute("INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, '2026-10-01')", (hotel_id,))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("DELETE FROM saved_hotels WHERE hotel_id='one'")
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("UPDATE demo_hotel_nights SET hotel_id='missing'")
        db.execute('UPDATE demo_hotel_nights SET nightly_rate_cents=0, rooms_available=0')
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('day', [None, '', '2026-1-01', '2026-01-1', '2026/01/01',
    '2026-02-29', '2026-04-31', '2026-13-01', '2026-00-01', '2026-01-00',
    '2026-01-32', '0000-01-01', '2026-10-01T00:00:00', '2026-10-01 ', 'not-a-date'])
def test_invalid_stay_dates_rejected(database: Database, day) -> None:
    with database.connect() as db:
        db.execute(HOTEL_INSERT, ('one', None, None, 0, 0))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('INSERT INTO demo_hotel_nights (hotel_id, stay_date) VALUES (?, ?)', ('one', day))


@pytest.mark.parametrize('column', ['nightly_rate_cents', 'rooms_available'])
@pytest.mark.parametrize('value', [None, -1, 1.5, 'invalid', float('inf')])
def test_invalid_daily_values_rejected(database: Database, column: str, value) -> None:
    with database.connect() as db:
        db.execute(HOTEL_INSERT, ('one', None, None, 0, 0))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(f'INSERT INTO demo_hotel_nights (hotel_id, stay_date, {column}) VALUES (?, ?, ?)',
                       ('one', '2026-10-01', value))


def test_failed_migration_rolls_back_and_can_be_retried(database: Database) -> None:
    downgrade_fixture_to_v2(database)
    before = legacy_snapshot(database)
    with database.connect() as db:
        db.execute('CREATE TABLE demo_hotel_nights (conflicting_schema TEXT)')
    with pytest.raises(sqlite3.OperationalError):
        database.initialize()
    with database.connect() as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 2
        assert db.execute("SELECT name FROM sqlite_master WHERE name='saved_hotels'").fetchone() is None
        db.execute('DROP TABLE demo_hotel_nights')
    database.initialize()
    assert legacy_snapshot(database) == before


def test_unknown_schema_version_rejected_without_changes(database: Database) -> None:
    with database.connect() as db:
        db.execute('PRAGMA user_version = 999')
    before = database.path.read_bytes()
    with pytest.raises(RuntimeError, match='Unsupported database schema version'):
        database.initialize()
    assert database.path.read_bytes() == before
