# ZIP lookup controller contract

`backend/app/controllers/locations.py` exposes
`lookup_zip(postcode: str) -> ZipLocation | None`. The fixed demo endpoint
uses `"16802"`; the parameterized endpoint accepts any five-digit U.S. ZIP code. Automated tests use mocked responses and fictional values, with no
provider calls.

The function accepts exactly five ASCII digits as a string, retaining leading
zeros. Invalid input raises `ValueError` before any request. It reads the key
through `backend/app/config.py`; the key stays in the backend request.

The request follows the [Geoapify forward geocoding documentation](https://apidocs.geoapify.com/docs/geocoding/):
GET the fixed `/v1/geocode/search` endpoint with `postcode`, `type=postcode`,
`filter=countrycode:us`, `format=json`, and the backend-only `apiKey` parameter.
It uses the existing HTTPX transport with 10-second connect/read/write/pool
timeouts, no retries, and no redirect following. These are operation timeouts,
not an overall wall-clock deadline. Using the transport directly avoids the
HTTPX client's INFO log of full request URLs.

The function scans results in provider order and accepts the first entry with
the exact requested postcode, U.S. country code (case-insensitive),
`result_type=postcode`, and finite numeric latitude/longitude in the ranges
[-90, 90] and [-180, 180]. Booleans, numeric strings, and missing coordinates
are rejected.

| Outcome | Contract |
| --- | --- |
| Verified match | A small dictionary with `postcode`, `country_code` (`us`), `latitude`, and `longitude`. Optional `locality` uses the first nonblank city, town, village, or municipality. |
| Unresolved ZIP | `None`: a valid results list is empty or contains no acceptable matching location. No nearby or mismatched result is substituted. |
| Missing configuration | `GeoapifyConfigurationError`, a subclass of `GeoapifyRequestError`, with a fixed, credential-free message. No provider request. |
| Provider failure | `GeoapifyRequestError` with a fixed, credential-free message: HTTP/transport failure, invalid JSON, or a missing/invalid results list. |
| Invalid input | `ValueError` with a fixed validation message; no provider request. |

Provider bodies, key values, full request URLs, and raw transport exception text
are not returned or printed. Transport exception chaining is suppressed. Only
the selected location fields are returned; raw provider metadata is discarded.

The location has no price and is independent of hotel models, SQLite, accounts,
and booking logic. Both ZIP routes below invoke it. Vue's ZIP demonstration
panel calls only the local API through the existing backend proxy; the key
and provider request remain in the backend.
There are no dependency or environment variable changes. The existing root
`.env` setup and backend restart instructions still apply.

Verification: `cd backend` and run
`.venv/bin/python -m pytest -q tests/test_locations.py`. Tests replace the key
helper and transport, check outgoing parameters and timeout, and cover success,
mismatches, empty results, invalid coordinates, HTTP errors, timeout/connection
failures, malformed payloads, and credential-safe output and errors.

## Demo route

`GET /api/demo/zip-location` is a thin FastAPI route that always calls
`lookup_zip("16802")`. It accepts no ZIP input and contains no provider logic.
The response schema keeps only the small location fields described above.

| HTTP status | Response |
| --- | --- |
| 200 | Verified location dictionary, with `locality` only if present. |
| 503 | `{"detail":"Geoapify key is not configured."}` |
| 404 | `{"detail":"ZIP 16802 could not be resolved."}` |
| 502 | `{"detail":"Location provider request failed."}` |

Errors use fixed text, never the underlying exception message. Existing routes,
including both health checks, retain their behavior.

Start the backend using the README instructions and existing environment.
With the default port, the local demo URL is
`http://127.0.0.1:8000/api/demo/zip-location`. Each visit attempts a live lookup
when configured. Configuration health alone does not verify provider access.
The route tests use a mocked controller and temporary databases:
`.venv/bin/python -m pytest -q tests/test_zip_route.py` from `backend/`.

## Parameterized lookup

`GET /api/zip-location?postcode=16802` passes the query string to the same
controller. `postcode` is required and must contain exactly five ASCII digits;
FastAPI returns 422 before calling the controller for invalid or missing input.
The parameter remains a string so a ZIP such as `00501` keeps its leading zeros.
Success and provider/configuration errors use the same response contract as the
demo route. The 404 detail identifies the requested ZIP.

`ZipLookupPanel.vue` now presents a labeled ZIP input and submits it through
`useZipLookup.js` and `frontend/src/api/locations.js`. The form trims surrounding
spaces, validates five digits, disables input and submission while loading, and
clears prior results/errors on a new request or an input edit. A mismatched ZIP
in a successful response is rejected. The result table displays ZIP, country,
locality (or "Not provided"), latitude, and longitude. Its caption identifies
the returned ZIP. The existing hotel-name search remains separate.

The frontend key never exists in a `VITE_` variable or request. No dependency,
hotel model, database persistence, map, or shortlist changes are needed.
