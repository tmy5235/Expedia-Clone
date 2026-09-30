"""Resolve U.S. ZIP codes without involving hotel prices or persistence."""

import math
import re
from typing import NotRequired, TypedDict

import httpx

from app.config import load_geoapify_api_key


class ZipLocation(TypedDict):
    postcode: str
    country_code: str
    latitude: float
    longitude: float
    locality: NotRequired[str]


class GeoapifyRequestError(RuntimeError):
    """A configuration or provider failure, with a credential-free message."""


class GeoapifyConfigurationError(GeoapifyRequestError):
    """The backend has no configured provider key."""


class GeoapifyRateLimitError(GeoapifyRequestError):
    """Provider quota or request rate was exceeded."""


def request_geoapify(path: str, parameters: dict[str, str | int]) -> object:
    """Send one credential-safe request to a fixed Geoapify API path."""
    key = load_geoapify_api_key()
    if not key:
        raise GeoapifyConfigurationError("Geoapify key is not configured.")

    request = httpx.Request(
        "GET", f"https://api.geoapify.com{path}",
        params={**parameters, "apiKey": key},
        extensions={"timeout": httpx.Timeout(10.0).as_dict()},
    )
    try:
        # The transport avoids Client's INFO log of the credential-bearing URL.
        # No redirects or retries: the key is sent only to the fixed provider.
        with httpx.HTTPTransport(retries=0) as transport:
            response = transport.handle_request(request)
            try:
                if response.status_code == 429:
                    raise GeoapifyRateLimitError("Geoapify request failed.")
                if not response.is_success:
                    raise GeoapifyRequestError("Geoapify request failed.")
                response.read()
                payload = response.json()
            finally:
                response.close()
    except (httpx.HTTPError, ValueError):
        raise GeoapifyRequestError("Geoapify request failed.") from None
    return payload


def lookup_zip(postcode: str) -> ZipLocation | None:
    """Return a verified location, None if unresolved, or a safe provider error."""
    if not isinstance(postcode, str) or re.fullmatch(r"[0-9]{5}", postcode) is None:
        raise ValueError("Enter a five-digit U.S. ZIP code as a string.")
    payload = request_geoapify("/v1/geocode/search", {
        "postcode": postcode, "type": "postcode",
        "filter": "countrycode:us", "format": "json",
    })

    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise GeoapifyRequestError("Geoapify returned an invalid response.")
    for result in payload["results"]:
        if not isinstance(result, dict):
            continue
        if (result.get("postcode") != postcode
                or str(result.get("country_code", "")).lower() != "us"
                or result.get("result_type") != "postcode"):
            continue
        lat, lon = result.get("lat"), result.get("lon")
        if not all(type(value) in (int, float) for value in (lat, lon)):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        if not (math.isfinite(lat) and math.isfinite(lon)):
            continue
        location: ZipLocation = {
            "postcode": postcode, "country_code": "us",
            "latitude": float(lat), "longitude": float(lon),
        }
        for field in ("city", "town", "village", "municipality"):
            locality = result.get(field)
            if isinstance(locality, str) and locality.strip():
                location["locality"] = locality.strip()
                break
        return location
    return None
