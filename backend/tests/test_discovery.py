"""Repeatable provider/route checks. Every request is mocked; DBs are temporary."""
import logging
from pathlib import Path
import traceback

from fastapi.testclient import TestClient
import httpx
import pytest

from app import main
from app.controllers import discovery, locations

KEY = "fictional-discovery-key"
CENTER = {"postcode": "00501", "country_code": "us", "result_type": "postcode",
          "lat": 40.8, "lon": -73.04, "city": "Fictional Center"}


def feature(place_id="test-hotel", name="Fictional Hotel", coordinates=None):
    return {"type": "Feature", "geometry": {"type": "Point", "coordinates":
            coordinates if coordinates is not None else [-73.041, 40.801]},
            "properties": {"place_id": place_id, "name": name,
                           "formatted": "Fictional address", "secret": KEY}}


@pytest.fixture
def provider(monkeypatch):
    responses, requests = [], []
    monkeypatch.setattr(locations, "load_geoapify_api_key", lambda: KEY)
    monkeypatch.setattr(main, "load_geoapify_api_key", lambda: KEY)

    def handle(request):
        requests.append(request)
        result = responses.pop(0)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(locations.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handle))
    return responses, requests


def add_response(responses, features):
    responses.extend([
        httpx.Response(200, json={"results": [CENTER]}),
        httpx.Response(200, json={"type": "FeatureCollection", "features": features}),
    ])


def test_live_search_contract_and_credential_safety(provider, caplog):
    responses, requests = provider
    add_response(responses, [feature()])
    with caplog.at_level(logging.DEBUG):
        result = discovery.discover_hotels("00501").model_dump()
    assert result["center"]["postcode"] == "00501"
    assert result["radius_meters"] == 5000 and result["result_limit"] == 20
    assert result["hotels"] == [{"place_id": "test-hotel", "name": "Fictional Hotel",
        "address": "Fictional address", "latitude": 40.801, "longitude": -73.041}]
    assert result["provider"] == "geoapify"
    assert result["omitted_count"] == 0 and not result["limit_reached"]
    assert len(requests) == 2 and requests[0].url.params["postcode"] == "00501"
    assert requests[1].url.path == "/v2/places"
    assert dict(requests[1].url.params) == {
        "categories": "accommodation.hotel", "filter": "circle:-73.04,40.8,5000",
        "bias": "proximity:-73.04,40.8", "limit": "20", "apiKey": KEY,
    }
    assert KEY not in repr(result) + caplog.text


def test_empty_is_success_missing_fields_are_not_invented(provider):
    responses, _ = provider
    add_response(responses, [])
    assert discovery.discover_hotels("00501").hotels == []
    missing = feature(name=" ")
    missing["properties"].pop("formatted")
    add_response(responses, [missing])
    hotel = discovery.discover_hotels("00501").hotels[0]
    assert hotel.name is None and hotel.address is None
    assert "price" not in hotel.model_dump()


def test_invalid_and_duplicate_places_omitted_with_disclosure(provider):
    responses, _ = provider
    add_response(responses, [feature(), feature(), None, {}, feature(place_id=""),
        feature(place_id="far", coordinates=[0, 0]),
        feature(place_id="bad", coordinates=["-73", 40]),
        feature(place_id="bool", coordinates=[True, 40]),
        feature(place_id="range", coordinates=[-181, 40])])
    result = discovery.discover_hotels("00501")
    assert len(result.hotels) == 1 and result.omitted_count == 8


def test_result_limit_and_no_automatic_pagination(provider):
    responses, requests = provider
    add_response(responses, [feature(place_id=f"hotel-{i}") for i in range(21)])
    result = discovery.discover_hotels("00501")
    assert len(result.hotels) == 20 and result.limit_reached and result.omitted_count == 1
    assert len(requests) == 2


@pytest.mark.parametrize("center", [None, {**CENTER, "postcode": "10001"},
    {**CENTER, "country_code": "ca"}, {**CENTER, "result_type": "city"}])
def test_unresolved_never_requests_places(provider, center):
    responses, requests = provider
    responses.append(httpx.Response(200, json={"results": [] if center is None else [center]}))
    with pytest.raises(discovery.UnresolvedZipError):
        discovery.discover_hotels("00501")
    assert len(requests) == 1


@pytest.mark.parametrize("body", [None, {}, [], {"type": "FeatureCollection", "features": None}])
def test_malformed_places_are_failure_not_empty(provider, body):
    responses, _ = provider
    responses.extend([httpx.Response(200, json={"results": [CENTER]}), httpx.Response(200, json=body)])
    with pytest.raises(locations.GeoapifyRequestError):
        discovery.discover_hotels("00501")


@pytest.mark.parametrize("stage", ["geocoding", "places"])
@pytest.mark.parametrize("status,expected", [(429, 429), (403, 502), (500, 502)])
def test_provider_errors_at_either_stage_are_safe(tmp_path: Path, provider, caplog, stage, status, expected):
    responses, _ = provider
    if stage == "places":
        responses.append(httpx.Response(200, json={"results": [CENTER]}))
    responses.append(httpx.Response(status, text=KEY))
    with TestClient(main.create_app(tmp_path / "test.sqlite3")) as client:
        response = client.get("/api/discovery/hotels?postcode=00501")
    assert response.status_code == expected
    assert "hotels" not in response.json()
    assert KEY not in response.text + caplog.text
    if status == 429:
        assert "limit" in response.json()["detail"]


def test_timeout_does_not_leak_key_or_become_empty(provider):
    responses, _ = provider
    responses.extend([httpx.Response(200, json={"results": [CENTER]}), httpx.ReadTimeout(KEY)])
    with pytest.raises(locations.GeoapifyRequestError) as error:
        discovery.discover_hotels("00501")
    assert KEY not in "".join(traceback.format_exception(error.value))


def test_route_validation_success_unresolved_and_configuration(tmp_path: Path, provider, monkeypatch):
    responses, requests = provider
    with TestClient(main.create_app(tmp_path / "test.sqlite3")) as client:
        for value in ["", "1234", "123456", "abcde", "００５０１"]:
            assert client.get("/api/discovery/hotels", params={"postcode": value}).status_code == 422
        assert client.get("/api/discovery/hotels").status_code == 422
        assert requests == []
        add_response(responses, [feature()])
        response = client.get("/api/discovery/hotels?postcode=00501")
        assert response.status_code == 200
        assert response.headers["Cache-Control"] == "no-store"
        assert response.json()["hotels"][0]["place_id"] == "test-hotel"
        responses.append(httpx.Response(200, json={"results": []}))
        response = client.get("/api/discovery/hotels?postcode=00501")
        assert response.status_code == 404 and "00501" in response.json()["detail"]
        monkeypatch.setattr(locations, "load_geoapify_api_key", lambda: "")
        assert client.get("/api/discovery/hotels?postcode=00501").status_code == 503
        assert client.get("/health").status_code == 200
