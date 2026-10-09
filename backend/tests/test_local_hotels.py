"""Local storage, rollback and restart tests with temporary databases only."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.database import Database
from app.main import create_app
from app.controllers.local_hotels import LocalHotelController
from app.local_hotel_schemas import SaveLocalHotel
from app.saved_hotels import SavedHotelStore


PAYLOAD = {'hotel': {'place_id': ' 00Provider/ABC?x=1#two ', 'name': None, 'address': None,
                    'latitude': 40.801, 'longitude': -73.041},
           'center': {'postcode': '00501', 'country_code': 'us', 'locality': 'Fictional Center',
                      'latitude': 40.8, 'longitude': -73.04}}


@pytest.fixture
def storage(tmp_path: Path):
    path = tmp_path / 'local.sqlite3'
    with TestClient(create_app(path)) as client:
        yield client, Database(path)


def legacy_rows(database: Database) -> dict:
    with database.connect() as db:
        return {table: [tuple(row) for row in db.execute(f'SELECT * FROM {table} ORDER BY rowid')]
                for table in ('hotels', 'trips', 'users', 'bookings', 'sessions', 'search_history')}


def test_save_search_status_repeat_and_restart(storage):
    client, database = storage
    original = legacy_rows(database)
    assert client.get('/api/local-hotels?postcode=00501').json()['hotels'] == []
    response = client.post('/api/local-hotels', json=PAYLOAD)
    assert response.status_code == 200
    expected_nights = [{'stay_date': f'2026-10-{day}', 'nightly_rate_cents': 10000, 'rooms_available': 20}
                       for day in range(10, 15)]
    assert response.json() == {**PAYLOAD['hotel'], 'demo_nights': expected_nights}
    with database.connect() as db:
        db.execute('UPDATE demo_hotel_nights SET nightly_rate_cents=12345, rooms_available=3 WHERE stay_date=?',
                   ('2026-10-10',))
    for _ in range(2):
        assert client.post('/api/local-hotels', json=PAYLOAD).status_code == 200
    with TestClient(create_app(database.path)) as restarted:
        result = restarted.get('/api/local-hotels?postcode=00501')
        assert result.headers['cache-control'] == 'no-store'
        assert result.json()['center'] == PAYLOAD['center']
        assert result.json()['source'] == 'local'
        assert result.json()['hotels'][0]['place_id'] == PAYLOAD['hotel']['place_id']
        assert result.json()['hotels'][0]['demo_nights'][0] == {
            'stay_date': '2026-10-10', 'nightly_rate_cents': 12345, 'rooms_available': 3}
        assert restarted.post('/api/local-hotels/status', json={'place_ids': [PAYLOAD['hotel']['place_id'], 'missing']}).json() == {
            'saved_ids': [PAYLOAD['hotel']['place_id']]}
    with database.connect() as db:
        assert [db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in
                ('saved_hotels', 'saved_hotel_zips', 'saved_search_locations', 'demo_hotel_nights')] == [1, 1, 1, 5]
    assert legacy_rows(database) == original


def test_multiple_zip_associations_and_atomic_removal_preserve_other_records(storage):
    client, database = storage
    before = legacy_rows(database)
    client.post('/api/local-hotels', json=PAYLOAD)
    second_zip = deepcopy(PAYLOAD)
    second_zip['center']['postcode'] = '00502'
    client.post('/api/local-hotels', json=second_zip)
    other_hotel = deepcopy(PAYLOAD)
    other_hotel['hotel']['place_id'] = 'unrelated-hotel'
    client.post('/api/local-hotels', json=other_hotel)
    assert len(client.get('/api/local-hotels?postcode=00501').json()['hotels']) == 2
    assert len(client.get('/api/local-hotels?postcode=00502').json()['hotels']) == 1
    assert client.get('/api/local-hotels?postcode=00503').json()['hotels'] == []
    for _ in range(2):  # Idempotent delete, even after another tab removed it.
        response = client.delete('/api/local-hotels', params={'hotel_id': PAYLOAD['hotel']['place_id']})
        assert response.status_code == 204
    assert client.get('/api/local-hotels?postcode=00502').json() == {
        'provider': 'geoapify', 'source': 'local', 'center': None, 'radius_meters': 5000, 'hotels': []}
    assert [h['place_id'] for h in client.get('/api/local-hotels?postcode=00501').json()['hotels']] == ['unrelated-hotel']
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM demo_hotel_nights').fetchone()[0] == 5
        assert [tuple(r) for r in db.execute('SELECT * FROM saved_hotel_zips')] == [('unrelated-hotel', '00501')]
        assert [r[0] for r in db.execute('SELECT postcode FROM saved_search_locations')] == ['00501']
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
    with TestClient(create_app(database.path)) as restarted:
        assert restarted.get('/api/local-hotels?postcode=00502').json()['hotels'] == []
    assert legacy_rows(database) == before


@pytest.mark.parametrize('section,key,value', [
    ('hotel', 'place_id', ''), ('hotel', 'place_id', ' '), ('hotel', 'place_id', 123),
    ('hotel', 'latitude', 91), ('hotel', 'longitude', -181), ('hotel', 'latitude', True),
    ('hotel', 'latitude', '40.8'), ('hotel', 'latitude', None), ('hotel', 'longitude', 0),
    ('hotel', 'nightly_rate_cents', 1), ('hotel', 'name', {}),
    ('center', 'postcode', '501'), ('center', 'postcode', 501), ('center', 'country_code', 'ca'),
    ('center', 'latitude', 91), ('center', 'longitude', 'invalid'),
])
def test_save_validates_payload_without_writes(storage, section, key, value):
    client, database = storage
    body = deepcopy(PAYLOAD)
    body[section][key] = value
    assert client.post('/api/local-hotels', json=body).status_code == 422
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM saved_hotels').fetchone()[0] == 0


def test_query_and_status_validation(storage):
    client, _ = storage
    for value in ('501', '000000', 'abcde', '１２３４５'):
        assert client.get('/api/local-hotels', params={'postcode': value}).status_code == 422
    assert client.post('/api/local-hotels/status', json={'place_ids': ['x'] * 21}).status_code == 422
    assert client.post('/api/local-hotels/status', json={'place_ids': []}).json() == {'saved_ids': []}
    assert client.delete('/api/local-hotels', params={'hotel_id': ' '}).status_code == 422


def test_save_and_delete_failures_roll_back(storage):
    client, database = storage
    with database.connect() as db:
        db.execute("""CREATE TRIGGER fail_night BEFORE INSERT ON demo_hotel_nights
            WHEN NEW.stay_date='2026-10-12' BEGIN SELECT RAISE(ABORT, 'simulated failure'); END""")
    assert client.post('/api/local-hotels', json=PAYLOAD).status_code == 503
    with database.connect() as db:
        assert all(db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] == 0 for t in
                   ('saved_hotels', 'demo_hotel_nights', 'saved_hotel_zips', 'saved_search_locations'))
        db.execute('DROP TRIGGER fail_night')
    assert client.post('/api/local-hotels', json=PAYLOAD).status_code == 200
    before = client.get('/api/local-hotels?postcode=00501').json()
    with database.connect() as db:
        db.execute("""CREATE TRIGGER fail_delete BEFORE DELETE ON saved_hotels
            BEGIN SELECT RAISE(ABORT, 'simulated failure'); END""")
    assert client.delete('/api/local-hotels', params={'hotel_id': PAYLOAD['hotel']['place_id']}).status_code == 503
    assert client.get('/api/local-hotels?postcode=00501').json() == before


def test_concurrent_saves_are_idempotent(storage):
    _, database = storage
    controller = LocalHotelController(SavedHotelStore(database))
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: controller.save(SaveLocalHotel(**PAYLOAD)), range(8)))
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM saved_hotels').fetchone()[0] == 1
        assert db.execute('SELECT count(*) FROM demo_hotel_nights').fetchone()[0] == 5
        assert db.execute('SELECT count(*) FROM saved_hotel_zips').fetchone()[0] == 1


@pytest.mark.parametrize('lock_kind', ['pending_edit', 'open_reader'])
def test_remove_lock_message_rollback_and_retry(storage, lock_kind):
    client, database = storage
    assert client.post('/api/local-hotels', json=PAYLOAD).status_code == 200
    before = client.get('/api/local-hotels?postcode=00501').json()
    # Model DB Browser's pending edits, and a reader that prevents commit.
    # The latter proves partial deletion rolls back even if it reaches commit.
    blocker = sqlite3.connect(database.path)
    try:
        blocker.execute('BEGIN IMMEDIATE' if lock_kind == 'pending_edit' else 'BEGIN')
        blocker.execute('SELECT * FROM saved_hotels').fetchall()
        response = client.delete('/api/local-hotels', params={'hotel_id': PAYLOAD['hotel']['place_id']})
        assert response.status_code == 503
        assert response.json()['detail'] == (
            'Database is busy. Save or revert pending edits in DB Browser for SQLite, then try again.')
    finally:
        blocker.rollback()
        blocker.close()
    assert client.get('/api/local-hotels?postcode=00501').json() == before
    assert client.delete('/api/local-hotels', params={'hotel_id': PAYLOAD['hotel']['place_id']}).status_code == 204
    assert client.get('/api/local-hotels?postcode=00501').json()['hotels'] == []
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM demo_hotel_nights').fetchone()[0] == 0
        assert db.execute('SELECT count(*) FROM saved_hotel_zips').fetchone()[0] == 0
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


def test_v3_migration_preserves_existing_saved_hotels_and_nights(storage, tmp_path):
    client, database = storage
    client.post('/api/local-hotels', json=PAYLOAD)
    with database.connect() as db:
        before = [tuple(r) for r in db.execute('SELECT * FROM saved_hotels')]
        nights = [tuple(r) for r in db.execute('SELECT * FROM demo_hotel_nights')]
        db.execute('DROP TABLE saved_hotel_zips')
        db.execute('DROP TABLE saved_search_locations')
        db.execute('PRAGMA user_version=3')
    for _ in range(2):
        Database(database.path, tmp_path / 'no-seed-files').initialize()
    with database.connect() as db:
        assert [tuple(r) for r in db.execute('SELECT * FROM saved_hotels')] == before
        assert [tuple(r) for r in db.execute('SELECT * FROM demo_hotel_nights')] == nights
        assert db.execute('PRAGMA user_version').fetchone()[0] == 5
        assert db.execute('SELECT count(*) FROM saved_hotel_zips').fetchone()[0] == 0
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO saved_hotel_zips VALUES ('unknown', '00501')")
