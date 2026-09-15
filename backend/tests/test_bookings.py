from pathlib import Path
import sqlite3

from fastapi.testclient import TestClient
import pytest

from app.database import Database
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    with TestClient(create_app(tmp_path / 'test.sqlite3')) as test_client:
        yield test_client


def test_seeded_users_and_history(client: TestClient) -> None:
    users = client.get('/api/users').json()
    assert [user['user_id'] for user in users] == [f'U00{i}' for i in range(1, 7)]
    history = client.get('/api/bookings', params={'user_id': 'U001'}).json()
    assert {b['booking_id'] for b in history} == {'B001', 'B002'}
    assert next(b for b in history if b['booking_id'] == 'B001')['total_cents'] == 30000
    assert client.get('/api/bookings', params={'user_id': 'U006'}).json() == []


def test_crud_persists_and_does_not_reseed(tmp_path: Path) -> None:
    path = tmp_path / 'persist.sqlite3'
    with TestClient(create_app(path)) as client:
        first = client.post('/api/bookings', json={'user_id': 'U006', 'trip_id': 'T001'})
        second = client.post('/api/bookings', json={'user_id': 'U006', 'trip_id': 'T009'})
        assert first.status_code == second.status_code == 201
        first_id, second_id = first.json()['booking_id'], second.json()['booking_id']
        assert first_id != second_id
        assert client.patch(f'/api/bookings/{first_id}', json={'user_id': 'U006', 'status': 'cancelled'}).json()['status'] == 'cancelled'
        assert client.delete(f'/api/bookings/{second_id}', params={'user_id': 'U006'}).status_code == 204
        assert client.delete('/api/bookings/B001', params={'user_id': 'U001'}).status_code == 204
    for _ in range(2):
        with TestClient(create_app(path)) as client:
            history = client.get('/api/bookings', params={'user_id': 'U006'}).json()
            assert len(history) == 1
            assert history[0]['booking_id'] == first_id
            assert history[0]['status'] == 'cancelled'
            assert [b['booking_id'] for b in client.get('/api/bookings', params={'user_id': 'U001'}).json()] == ['B002']
    with sqlite3.connect(path) as db:
        assert [db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] for table in ('hotels', 'trips', 'users', 'bookings')] == [8, 12, 6, 6]


@pytest.mark.parametrize('payload', [
    {'user_id': 'unknown', 'trip_id': 'T001'},
    {'user_id': 'U001', 'trip_id': 'unknown'},
    {'user_id': "U001' OR 1=1 --", 'trip_id': 'T001'},
])
def test_invalid_booking_references(client: TestClient, payload: dict) -> None:
    assert client.post('/api/bookings', json=payload).status_code in (404, 422)
    assert len(client.get('/api/bookings', params={'user_id': 'U001'}).json()) == 2


def test_validate_status_and_owner(client: TestClient) -> None:
    assert client.patch('/api/bookings/B001', json={'user_id': 'U001', 'status': 'confirmed'}).status_code == 422
    assert client.patch('/api/bookings/B001', json={'user_id': 'U002', 'status': 'cancelled'}).status_code == 404
    assert client.delete('/api/bookings/B001', params={'user_id': 'U002'}).status_code == 404
    assert client.delete('/api/bookings/missing', params={'user_id': 'U001'}).status_code == 404
    assert client.get('/api/bookings', params={'user_id': 'missing'}).status_code == 404
    assert client.get('/api/bookings', params={'user_id': 'two words'}).status_code == 422
    assert client.post('/api/bookings', json={'user_id': '', 'trip_id': 'T001'}).status_code == 422
    assert client.post('/api/bookings', json={'user_id': 'U001', 'trip_id': 'T001', 'status': 'cancelled'}).status_code == 422
    for _ in range(2):
        assert client.patch('/api/bookings/B001', json={'user_id': 'U001', 'status': 'cancelled'}).status_code == 200
    assert client.patch('/api/bookings/two words', json={'user_id': 'U001', 'status': 'cancelled'}).status_code == 422
    assert client.delete('/api/bookings/two words', params={'user_id': 'U001'}).status_code == 422


def test_sqlite_is_source_after_seeding_and_enforces_foreign_keys(tmp_path: Path) -> None:
    path = tmp_path / 'source.sqlite3'
    database = Database(path)
    database.initialize()
    with database.connect() as db:
        db.execute('UPDATE hotels SET hotel_name = ? WHERE hotel_id = ?', ('SQLite Only Hotel', 'H001'))
        with pytest.raises(sqlite3.IntegrityError):
            db.execute("INSERT INTO bookings VALUES ('bad', 'missing', 'T001', '2026-09-15', 'confirmed')")
    # Restart without any accessible CSV files. All reads must still work.
    database = Database(path, tmp_path / 'no-csv-files')
    database.initialize()
    assert len(database.search('sqlite only')) == 2
    assert database.search('Harbor Lantern') == []
    assert database.search('%') == []
    assert database.search("' OR 1=1 --") == []
    assert len(database.users()) == 6
    assert len(database.history('U001')) == 2


def test_seed_failure_rolls_back_schema_and_rows(tmp_path: Path) -> None:
    from app.hotel_search import HotelDataError
    database = Database(tmp_path / 'atomic.sqlite3', tmp_path / 'missing')
    with pytest.raises(HotelDataError):
        database.initialize()
    with database.connect() as db:
        assert db.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall() == []
    Database(database.path).initialize()
    assert len(Database(database.path).users()) == 6
