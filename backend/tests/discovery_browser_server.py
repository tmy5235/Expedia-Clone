"""Explicitly simulated browser verification, never imported by the normal app.

From backend/: EXPEDIA_DB_PATH=/tmp/expedia-discovery-check.sqlite3
  .venv/bin/python -m uvicorn tests.discovery_browser_server:app --port 8001
Use frontend port 5174 with EXPEDIA_API_TARGET=http://127.0.0.1:8001.
00501 = two fictional places, 00000 = unresolved, 99999 = empty,
11111 = simulated failure, 22222 = simulated rate limit.
No Geoapify network calls; map imagery still uses the normal tile provider.
"""
import time

import httpx

from app.controllers import locations
from app.main import create_app


def simulated_provider(path: str, parameters: dict[str, str | int]) -> object:
    if path == "/v1/geocode/search":
        postcode = parameters["postcode"]
        time.sleep(0.5)
        if postcode == "00000":
            return {"results": []}
        if postcode == "11111":
            raise locations.GeoapifyRequestError("Simulated outage")
        if postcode == "22222":
            raise locations.GeoapifyRateLimitError("Simulated quota")
        # Distinct center encodes only the explicit empty fixture, not a real ZIP.
        return {"results": [{"postcode": postcode, "country_code": "us",
            "result_type": "postcode", "lat": 40.8,
            "lon": -73.04 if postcode != "99999" else -73.05,
            "city": "SIMULATED TEST DATA"}]}
    if parameters["filter"] == "circle:-73.05,40.8,5000":
        return {"type": "FeatureCollection", "features": []}
    return {"type": "FeatureCollection", "features": [
        {"type": "Feature", "properties": {"place_id": "fixture-one",
            "name": "Fictional Hotel <text>", "formatted": "Fictional test address"},
         "geometry": {"type": "Point", "coordinates": [-73.041, 40.801]}},
        {"type": "Feature", "properties": {"place_id": "fixture-two"},
         "geometry": {"type": "Point", "coordinates": [-73.035, 40.803]}},
    ]}


# Refuse accidental provider traffic anywhere in this dedicated test process.
def no_network(*args, **kwargs):
    raise AssertionError("Live provider traffic is disabled in the fixture server")


httpx.HTTPTransport = no_network
locations.request_geoapify = simulated_provider
app = create_app()
