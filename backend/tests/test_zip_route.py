from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
import pytest

from app import main
from app.controllers import locations


@pytest.fixture
def route_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    lookup = Mock()
    monkeypatch.setattr(locations, "lookup_zip", lookup)
    monkeypatch.setattr(main, "load_geoapify_api_key", lambda: "")
    with TestClient(main.create_app(tmp_path / "route.sqlite3")) as client:
        yield client, lookup


@pytest.mark.parametrize("locality", [None, "Fictional Test Locality"])
def test_demo_route_returns_only_location_fields(route_client, locality) -> None:
    client, lookup = route_client
    expected = {
        "postcode": "16802", "country_code": "us",
        "latitude": 40.8, "longitude": -77.86,
    }
    if locality is not None:
        expected["locality"] = locality
    lookup.return_value = {**expected, "unexpected_metadata": "fictional-secret"}
    response = client.get("/api/demo/zip-location")
    assert response.status_code == 200
    assert response.json() == expected
    lookup.assert_called_once_with("16802")
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/api/health").json() == {
        "status": "ok", "geoapify": "key is not configured",
    }


def test_demo_route_unresolved_zip(route_client) -> None:
    client, lookup = route_client
    lookup.return_value = None
    response = client.get("/api/demo/zip-location")
    assert response.status_code == 404
    assert response.json() == {"detail": "ZIP 16802 could not be resolved."}
    lookup.assert_called_once_with("16802")


@pytest.mark.parametrize("error_type,status,detail", [
    (locations.GeoapifyConfigurationError, 503, "Geoapify key is not configured."),
    (locations.GeoapifyRequestError, 502, "Location provider request failed."),
])
def test_demo_route_errors_do_not_echo_exception(
    route_client, caplog, capsys, error_type, status, detail,
) -> None:
    client, lookup = route_client
    lookup.side_effect = error_type(
        "https://api.geoapify.com/v1/geocode/search?apiKey=fictional-secret",
    )
    response = client.get("/api/demo/zip-location")
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    assert "fictional-secret" not in response.text + caplog.text
    assert "api.geoapify.com" not in response.text + caplog.text
    assert capsys.readouterr() == ("", "")
    lookup.assert_called_once_with("16802")


@pytest.mark.parametrize("postcode", ["16802", "10001", "00501"])
def test_entered_zip_is_passed_to_controller(route_client, postcode: str) -> None:
    client, lookup = route_client
    expected = {
        "postcode": postcode, "country_code": "us",
        "latitude": 40.8, "longitude": -77.86,
    }
    lookup.return_value = {**expected, "private_metadata": "fictional-secret"}
    response = client.get("/api/zip-location", params={"postcode": postcode})
    assert response.status_code == 200
    assert response.json() == expected
    lookup.assert_called_once_with(postcode)


@pytest.mark.parametrize("postcode", ["", "1680", "168020", "abcde", "１６８０２", " 16802 "])
def test_invalid_entered_zip_never_calls_provider(route_client, postcode: str) -> None:
    client, lookup = route_client
    assert client.get("/api/zip-location", params={"postcode": postcode}).status_code == 422
    lookup.assert_not_called()


def test_missing_entered_zip_never_calls_provider(route_client) -> None:
    client, lookup = route_client
    assert client.get("/api/zip-location").status_code == 422
    lookup.assert_not_called()


def test_entered_zip_unresolved_error_identifies_request(route_client) -> None:
    client, lookup = route_client
    lookup.return_value = None
    response = client.get("/api/zip-location", params={"postcode": "10001"})
    assert response.status_code == 404
    assert response.json() == {"detail": "ZIP 10001 could not be resolved."}
    lookup.assert_called_once_with("10001")


@pytest.mark.parametrize("error_type,status,detail", [
    (locations.GeoapifyConfigurationError, 503, "Geoapify key is not configured."),
    (locations.GeoapifyRequestError, 502, "Location provider request failed."),
])
def test_entered_zip_errors_are_safe(route_client, error_type, status, detail) -> None:
    client, lookup = route_client
    lookup.side_effect = error_type("fictional-secret")
    response = client.get("/api/zip-location", params={"postcode": "10001"})
    assert response.status_code == status
    assert response.json() == {"detail": detail}
    lookup.assert_called_once_with("10001")
