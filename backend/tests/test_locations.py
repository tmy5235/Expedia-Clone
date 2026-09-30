import logging
import traceback

import httpx
import pytest

from app.controllers import locations


FAKE_KEY = "fictional-test-key"
MATCH = {
    "postcode": "16802", "country_code": "us", "result_type": "postcode",
    "lat": 40.8, "lon": -77.86, "city": "Fictional Test Locality",
}


@pytest.fixture(autouse=True)
def mock_provider(monkeypatch: pytest.MonkeyPatch):
    """Every lookup uses a fake key and in-memory transport, never the network."""
    monkeypatch.setattr(locations, "load_geoapify_api_key", lambda: FAKE_KEY)
    responses = []
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        response = responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

    monkeypatch.setattr(
        locations.httpx, "HTTPTransport", lambda **kwargs: httpx.MockTransport(handler),
    )
    return responses, requests


def test_success_and_request_contract(mock_provider, caplog, capsys) -> None:
    responses, requests = mock_provider
    responses.append(httpx.Response(200, json={"results": [{**MATCH, "apiKey": FAKE_KEY}]}))
    with caplog.at_level(logging.DEBUG):
        location = locations.lookup_zip("16802")
    assert location == {
        "postcode": "16802", "country_code": "us", "latitude": 40.8,
        "longitude": -77.86, "locality": "Fictional Test Locality",
    }
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "GET"
    assert request.url.scheme == "https"
    assert request.url.host == "api.geoapify.com"
    assert request.url.path == "/v1/geocode/search"
    assert dict(request.url.params) == {
        "postcode": "16802", "type": "postcode", "filter": "countrycode:us",
        "format": "json", "apiKey": FAKE_KEY,
    }
    assert request.extensions["timeout"] == dict.fromkeys(
        ("connect", "read", "write", "pool"), 10.0,
    )
    assert FAKE_KEY not in repr(location) + caplog.text
    assert str(request.url) not in caplog.text
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("changes", [
    {"postcode": "16801"}, {"postcode": None}, {"postcode": 16802},
    {"country_code": "ca"}, {"country_code": None},
    {"result_type": "city"}, {"result_type": None},
    {"lat": None}, {"lat": "40.8"}, {"lat": True}, {"lon": False},
    {"lat": 90.1}, {"lat": -90.1}, {"lon": 180.1}, {"lon": -180.1},
])
def test_mismatched_or_invalid_location_is_unresolved(mock_provider, changes) -> None:
    responses, _ = mock_provider
    responses.append(httpx.Response(200, json={"results": [{**MATCH, **changes}]}))
    assert locations.lookup_zip("16802") is None


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity"])
def test_nonfinite_coordinates_are_unresolved(mock_provider, number) -> None:
    responses, _ = mock_provider
    responses.append(httpx.Response(200, text=(
        '{"results":[{"postcode":"16802","country_code":"us",'
        '"result_type":"postcode","lat":' + number + ',"lon":-77.86}]}'
    )))
    assert locations.lookup_zip("16802") is None


def test_scan_candidates_and_allow_missing_locality(mock_provider) -> None:
    responses, _ = mock_provider
    match = {**MATCH, "city": None, "country_code": "US"}
    responses.append(httpx.Response(200, json={"results": [
        None, {**MATCH, "postcode": "16801"}, match,
    ]}))
    location = locations.lookup_zip("16802")
    assert location is not None and location["country_code"] == "us"
    assert "locality" not in location


def test_empty_results_are_unresolved(mock_provider) -> None:
    responses, _ = mock_provider
    responses.append(httpx.Response(200, json={"results": []}))
    assert locations.lookup_zip("16802") is None


@pytest.mark.parametrize("status", [301, 401, 403, 429, 500, 503])
def test_http_failures_are_sanitized(mock_provider, caplog, status) -> None:
    responses, requests = mock_provider
    responses.append(httpx.Response(status, text=FAKE_KEY))
    with caplog.at_level(logging.DEBUG), pytest.raises(locations.GeoapifyRequestError) as error:
        locations.lookup_zip("16802")
    assert str(error.value) == "Geoapify request failed."
    assert FAKE_KEY not in str(error.value) + caplog.text
    assert len(requests) == 1


@pytest.mark.parametrize("exception", [httpx.ReadTimeout, httpx.ConnectError])
def test_transport_errors_hide_raw_exception(mock_provider, caplog, capsys, exception) -> None:
    responses, _ = mock_provider
    responses.append(exception("https://api.geoapify.com/v1/geocode/search?apiKey=" + FAKE_KEY))
    with caplog.at_level(logging.DEBUG), pytest.raises(locations.GeoapifyRequestError) as error:
        locations.lookup_zip("16802")
    rendered = "".join(traceback.format_exception(error.value))
    assert str(error.value) == "Geoapify request failed."
    assert FAKE_KEY not in rendered + caplog.text
    assert "https://api.geoapify.com" not in rendered + caplog.text
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("body", ["not json", "null", "[]", "{}", '{"results":null}'])
def test_malformed_response_is_a_provider_failure(mock_provider, body) -> None:
    responses, _ = mock_provider
    responses.append(httpx.Response(200, text=body))
    with pytest.raises(locations.GeoapifyRequestError):
        locations.lookup_zip("16802")


def test_missing_key_does_not_send_request(mock_provider, monkeypatch) -> None:
    _, requests = mock_provider
    monkeypatch.setattr(locations, "load_geoapify_api_key", lambda: "")
    with pytest.raises(locations.GeoapifyConfigurationError, match="not configured"):
        locations.lookup_zip("16802")
    assert requests == []


@pytest.mark.parametrize("value", [16802, "1680", "168020", " 16802 ", "abcde", "１６８０２"])
def test_invalid_input_does_not_send_request(mock_provider, value) -> None:
    _, requests = mock_provider
    with pytest.raises(ValueError, match="five-digit"):
        locations.lookup_zip(value)
    assert requests == []


def test_controller_preserves_an_entered_zip_with_leading_zeros(mock_provider) -> None:
    responses, requests = mock_provider
    responses.append(httpx.Response(200, json={"results": [{**MATCH, "postcode": "00501"}]}))
    result = locations.lookup_zip("00501")
    assert result is not None and result["postcode"] == "00501"
    assert requests[0].url.params["postcode"] == "00501"
