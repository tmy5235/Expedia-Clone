from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.database import Database
from app.main import create_app
from app.controllers.pricing import priced_stay
from app.controllers.search import SearchController


def account(client, username='user_a'):
    payload = {'username': username, 'password': 'made-up-demo'}
    created = client.post('/api/accounts', json=payload)
    assert created.status_code == 201
    response = client.post('/api/login', json=payload)
    assert response.status_code == 200
    return response.json()


def search(client, query='Valley Trail'):
    return client.get('/api/stays', params={'hotel_name': query})


def test_accounts_errors_logout_and_restart(tmp_path):
    path = tmp_path / 'accounts.db'
    with TestClient(create_app(path)) as client:
        user = account(client)
        assert 'password' not in user
        assert client.get('/api/session').json() == user
        duplicate = client.post('/api/accounts', json={'username': ' USER_A ', 'password': 'other'})
        assert duplicate.status_code == 409
        assert client.get('/api/session').json() == user
        for username, password in [('user_a', 'wrong'), ('missing', 'made-up-demo')]:
            assert client.post('/api/login', json={'username': username, 'password': password}).status_code == 401
            assert client.get('/api/session').json() is None
        assert client.post('/api/login', json={'username': 'USER_A', 'password': 'made-up-demo'}).status_code == 200
        cookie = client.cookies.get('expedia_session')
    with TestClient(create_app(path)) as client:
        client.cookies.set('expedia_session', cookie)
        assert client.get('/api/session').json() == user
        assert client.post('/api/logout').status_code == 204
        client.cookies.set('expedia_session', cookie)
        assert client.get('/api/session').json() is None
        assert client.post('/api/login', json={'username': 'user_a', 'password': 'made-up-demo'}).json() == user


@pytest.mark.parametrize('username,password', [('  ', 'demo'), ('ab', 'demo'), ('a b', 'demo'), ('a'*41, 'demo'), ('valid', ' '), ('valid', '')])
def test_invalid_account_inputs(tmp_path, username, password):
    with TestClient(create_app(tmp_path / 'validation.db')) as client:
        assert client.post('/api/accounts', json={'username': username, 'password': password}).status_code == 422


def test_price_threshold_normalization_users_queries_and_restart(tmp_path):
    path = tmp_path / 'pricing.db'
    with TestClient(create_app(path)) as client:
        user_a = account(client)
        for index, query in enumerate(['Valley Trail', ' valley trail ', 'VALLEY TRAIL', 'Valley Trail', 'valley trail'], 1):
            response = search(client, query)
            assert response.headers['cache-control'] == 'no-store'
            stay = response.json()[0]
            assert stay['nightly_rate_cents'] == (10000 if index <= 3 else 12000)
            assert stay['search_count'] == index
        booking = client.post('/api/bookings', json={'user_id': user_a['user_id'], 'trip_id': stay['trip_id'], 'search_id': stay['search_id']}).json()
        assert booking['total_cents'] == stay['total_cents']
        assert search(client, 'Valley').json()[0]['nightly_rate_cents'] == 10000
        user_b = account(client, 'user_b')
        assert search(client).json()[0]['nightly_rate_cents'] == 10000
        assert client.post('/api/bookings', json={'user_id': user_b['user_id'], 'trip_id': stay['trip_id'], 'search_id': stay['search_id']}).status_code == 404
        client.post('/api/logout')
        for _ in range(5):
            assert search(client).json()[0]['nightly_rate_cents'] == 10000
        assert search(client, '   ').status_code == 422
    with TestClient(create_app(path)) as client:
        client.post('/api/login', json={'username': 'user_a', 'password': 'made-up-demo'})
        assert search(client).json()[0]['search_count'] == 6
        assert client.get('/api/bookings', params={'user_id': user_a['user_id']}).json()[0]['total_cents'] == booking['total_cents']
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT nightly_rate_cents FROM hotels WHERE hotel_id='H008'").fetchone()[0] == 10000
        assert db.execute('SELECT count(*) FROM search_history').fetchone()[0] == 8
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []


@pytest.mark.parametrize('before,after', [
    ('2026-09-22T03:59:59+00:00', '2026-09-22T04:00:00+00:00'),
    ('2026-11-01T03:59:59+00:00', '2026-11-01T04:00:00+00:00'),
    ('2026-11-02T04:59:59+00:00', '2026-11-02T05:00:00+00:00'),
])
def test_new_york_midnight_resets_count(tmp_path, before, after):
    now = datetime.fromisoformat(before)
    with TestClient(create_app(tmp_path / 'day.db', clock=lambda: now)) as client:
        account(client)
        for _ in range(4):
            last = search(client).json()[0]
        assert last['nightly_rate_cents'] == 12000
        now = datetime.fromisoformat(after)
        stay = search(client).json()[0]
        assert stay['search_count'] == 1
        assert stay['nightly_rate_cents'] == 10000


def test_empty_results_recorded_blank_queries_ignored_and_concurrent_counts(tmp_path):
    database = Database(tmp_path / 'concurrent.db')
    database.initialize()
    user = database.create_account('test_user', 'demo')
    controller = SearchController(database, lambda: datetime(2026, 9, 22, 12, tzinfo=timezone.utc))
    assert controller.submit('missing', user) == []
    with pytest.raises(ValueError):
        controller.submit('   ', user)
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(lambda _: controller.submit('Valley Trail', user)[0], range(5)))
    assert sorted(row['search_count'] for row in results) == [1, 2, 3, 4, 5]
    assert sorted(row['nightly_rate_cents'] for row in results) == [10000, 10000, 10000, 12000, 12000]
    with database.connect() as db:
        assert db.execute('SELECT count(*) FROM search_history').fetchone()[0] == 6


def test_migrate_version_one_without_reseed_or_changed_relationships(tmp_path):
    path = tmp_path / 'legacy.db'
    # Exact pre-accounts schema shape, with a deleted starter record and custom booking.
    with sqlite3.connect(path) as db:
        db.executescript('''
            CREATE TABLE hotels (hotel_id TEXT PRIMARY KEY, hotel_name TEXT, city TEXT, state TEXT, nightly_rate_cents INTEGER);
            CREATE TABLE trips (trip_id TEXT PRIMARY KEY, hotel_id TEXT REFERENCES hotels(hotel_id), trip_name TEXT, check_in TEXT, check_out TEXT);
            CREATE TABLE users (user_id TEXT PRIMARY KEY, display_name TEXT);
            CREATE TABLE bookings (booking_id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(user_id), trip_id TEXT REFERENCES trips(trip_id), booked_on TEXT, status TEXT);
            INSERT INTO hotels VALUES ('H008', 'Valley Trail Inn', 'State College', 'PA', 10000);
            INSERT INTO trips VALUES ('T008', 'H008', 'Test stay', '2026-09-20', '2026-09-22');
            INSERT INTO users VALUES ('U006', 'Demo Traveler 6');
            INSERT INTO bookings VALUES ('custom', 'U006', 'T008', '2026-09-01', 'cancelled');
            PRAGMA user_version = 1;
        ''')
    for _ in range(2):
        Database(path, tmp_path / 'no-csvs').initialize()
    with sqlite3.connect(path) as db:
        assert db.execute('SELECT * FROM users').fetchall() == [('U006', 'Demo Traveler 6', 'traveler6', 'classroom-demo')]
        assert db.execute('SELECT * FROM bookings').fetchall() == [('custom', 'U006', 'T008', '2026-09-01', 'cancelled', 20000)]
        assert db.execute('PRAGMA foreign_key_check').fetchall() == []
        assert db.execute('PRAGMA user_version').fetchone()[0] == 5


def test_price_rounds_to_cents_and_does_not_mutate_base():
    stay = {'nightly_rate_cents': 10003, 'nights': 2}
    assert priced_stay(stay, 4)['nightly_rate_cents'] == 12004
    assert stay['nightly_rate_cents'] == 10003
