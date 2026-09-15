from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.hotel_search import HotelDataError, search_hotel_stays
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    with TestClient(create_app(tmp_path / "test.sqlite3")) as test_client:
        yield test_client


def test_search_returns_every_stay_for_matching_hotel() -> None:
    stays = search_hotel_stays("Harbor Lantern Hotel")

    assert [stay["trip_id"] for stay in stays] == ["T001", "T009"]
    assert stays[0] == {
        "trip_id": "T001",
        "trip_name": "Boston Harbor Weekend",
        "hotel_id": "H001",
        "hotel_name": "Harbor Lantern Hotel",
        "city": "Boston",
        "state": "MA",
        "check_in": "2026-09-18",
        "check_out": "2026-09-20",
        "nights": 2,
        "nightly_rate_cents": 15000,
        "total_cents": 30000,
    }


def test_search_is_case_insensitive_and_supports_partial_names() -> None:
    stays = search_hotel_stays("maple square")

    assert [stay["trip_id"] for stay in stays] == ["T002", "T010"]


def test_search_returns_empty_list_when_no_hotel_matches() -> None:
    assert search_hotel_stays("Oceanfront Resort") == []


def test_search_rejects_blank_hotel_name() -> None:
    with pytest.raises(ValueError, match="Enter a hotel name"):
        search_hotel_stays("   ")


def test_search_reports_missing_data_file(tmp_path: Path) -> None:
    with pytest.raises(HotelDataError, match="Unable to read hotels.csv"):
        search_hotel_stays("Harbor", tmp_path)


def test_stays_endpoint_returns_joined_results(client: TestClient) -> None:
    response = client.get("/api/stays", params={"hotel_name": "Harbor Lantern"})

    assert response.status_code == 200
    assert [stay["trip_id"] for stay in response.json()] == ["T001", "T009"]


def test_stays_endpoint_returns_empty_result(client: TestClient) -> None:
    response = client.get("/api/stays", params={"hotel_name": "Oceanfront Resort"})

    assert response.status_code == 200
    assert response.json() == []


def test_stays_endpoint_rejects_blank_query(client: TestClient) -> None:
    response = client.get("/api/stays", params={"hotel_name": "   "})

    assert response.status_code == 422
    assert response.json() == {"detail": "Enter a hotel name."}


def test_health_endpoint_responds(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
