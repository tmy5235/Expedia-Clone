# Hotel Finder

Repository: [Expedia-Clone](https://github.com/tmy5235/Expedia-Clone).

Assessed revision: [3e432bcb22d0cd24ae8e78538de1958deb6e8237](https://github.com/tmy5235/Expedia-Clone/commit/3e432bcb22d0cd24ae8e78538de1958deb6e8237).

Demo recording: **`IST 402 - Assignment 2.1 SR.mov`** (separate companion file).

## Overview

Hotel Finder accepts a five-digit U.S. ZIP code and displays nearby hotel
locations in a synchronized list and map. FastAPI verifies the exact ZIP through
Geoapify before requesting hotels within 5 km of the returned point. Vue handles
input and selection; Leaflet displays the map with OpenStreetMap tiles.

The returned point is the search center, not the user's device or every address
within the ZIP boundary. Each search requests one page of up to 20 places; coverage
varies and the results are not an exhaustive inventory. Missing names and addresses
are labeled honestly. Live places have no invented prices, ratings or availability.
The separate `/?demo=booking` page preserves the fictional account and booking demo.

## Run the app

Tested with Python 3.14.7 and Node 24.18.1. From a fresh checkout:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Create a project-root `.env` with `GEOAPIFY_API_KEY=your-own-local-key`.
The file is ignored and the key is used only by the backend. Restart FastAPI when
changing it. In separate terminals, from the repository root:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173. Vite proxies `/api` to FastAPI. `GET /api/health`
reports configuration status without disclosing the key. OSM tiles need no key.
See [README](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/README.md) for environment requirements and sample-account setup.

## Research and design

Research used official product help and API documentation on September 29, 2026.

| Source | Observation and resulting decision |
| --- | --- |
| [Google Hotels](https://support.google.com/travel/answer/6276008?hl=en) | A list/map pairing supports comparing locations. Adopt synchronized selection; omit price/review/booking controls unsupported by the data. |
| [Google Maps nearby search](https://support.google.com/maps/answer/4610185?co=GENIE.Platform%3DDesktop&hl=en) | Location-centered exploration is useful, but ordering alone does not explain a boundary. Show the verified ZIP center and 5 km circle. |
| [Geoapify geocoding](https://apidocs.geoapify.com/docs/geocoding/) and [Places](https://apidocs.geoapify.com/docs/places/) | Verify the requested U.S. postcode; use the hotel category and circle filter. Preserve provider IDs and honest missing fields. |
| [Leaflet](https://leafletjs.com/reference.html) | Use numbered markers and shared selection, explicit Enter/Space handling, text-only popups and map cleanup. |
| [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/) | Retain visible attribution and normal browser caching; avoid bulk/offline tile retrieval. |
| [Geoapify pricing](https://www.geoapify.com/pricing/) and [terms](https://www.geoapify.com/terms-and-conditions/) | Limit request volume with explicit submit, duplicate prevention and no automatic retries/pagination; simulate failures and rate limits. |

![Early mockup prepared before implementation](https://raw.githubusercontent.com/tmy5235/Expedia-Clone/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/screenshots/assignment2-early-mockup.svg)

The mockup established the ZIP form, numbered list/map selection and feedback
states. The final design uses a simpler header, hotel illustration and prominent
search card. Selected hotel coordinates remain visible; center coordinates are
in a disclosure. On narrow screens the list sits above the map. The illustration
and mockup are authored SVG; neither is a photograph of a returned property.
[Research notes](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/assignment2-research.md) record the design decisions.

## Architecture

| Layer | Responsibility |
| --- | --- |
| Model | Validated external-place schemas with provider IDs and coordinates; existing SQLite models preserve sample accounts and bookings. |
| Controller | Exact ZIP resolution, backend provider calls, radius enforcement, limits, normalization, deduplication and safe errors. |
| View | ZIP input, transient request state, honest feedback and selection shared by provider ID between list and map. |

An external hotel contains `place_id`, optional `name`/`address`, and numeric
latitude/longitude; it does not inherit the sample hotel's nightly rate.
[The API contract](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/assignment2-design.md) documents response fields and errors.
Discovery adds no SQLite tables or shortlist storage.

## Verification

Live ZIP: **16802**. Observation date: **September 29, 2026, America/New_York**.

| Input/action | Expected | Observed |
| --- | --- | --- |
| Live search | Exact center and nearby hotel places | State College, center 40.80317 / -77.86138; 20 cards/markers with cap notice. Count is an observation, not a fixed requirement. |
| List Enter / marker Space or Enter | Matching selection in both views | Scholar Hotel and Hampton Inn selections synchronized card, marker and popup |
| `123` | Validation without provider call | Five-digit feedback; stale results cleared |
| Simulated `00501` | Leading zero preserved; missing fields handled | Two fictional places and honest missing-name/address labels |
| Simulated empty/unresolved/failure/429 | Distinct outcomes | Empty response kept a center map; unresolved, failure and quota feedback remained errors |
| 390 px viewport | Usable responsive interface | No horizontal overflow; keyboard selection and attribution available |
| Automated checks | Preserve discovery and booking behavior | 117 backend tests, 32 frontend tests, both linters and production build passed |

![Live ZIP 16802 with matching selected card and marker](https://raw.githubusercontent.com/tmy5235/Expedia-Clone/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/screenshots/assignment2-final-results.png)

Additional views: [homepage](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/screenshots/assignment2-final-home.png) and
[mobile](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/screenshots/assignment2-final-mobile.png).

Run automated checks from the repository root:

```bash
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm test && npm run lint && npm run build)
```

[The verification guide](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/assignment2-verification.md) includes repeatable
simulated-browser instructions. Automated tests use mocked providers and temporary
SQLite files. Six live searches were made across development and final review;
no normal account or booking data was changed. The configured backend key was
absent from the frontend build, and `.env` remained ignored and untracked.

Limitations: one provider page, variable coverage and imagery, no forced live
quota exhaustion or real tile outage. One existing Starlette TestClient deprecation
warning remains. Original booking restart persistence is covered by temporary-
database regression tests.

## AI disclosure

**OpenAI Codex desktop with GPT-6 Astra** assisted with research, early mockup,
implementation, testing and documentation. The user confirmed the model, chose
the interface and approved the exact Leaflet 1.9.4 installation. Tools included
web research, terminal/file operations and browser automation. No additional AI
agent or image-generation model was used.

| Selected user prompt | Result |
| --- | --- |
| “For today we only want to implement part 1” | Separate live discovery without shortlist persistence |
| “Approve Leaflet 1.9.4 installation” | Environment check, exact installation and version/build verification |
| “make the layout or interface more simple like this image” | Simplified [discovery page](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/frontend/src/components/HotelDiscovery.vue) |
| “Just use Hotel Finder as the name” | Final branding and hotel-focused illustration |

Two failed approaches were corrected: markers were initially configured before
map bounds existed, and default marker Enter opened a popup without selecting the
list item. Initializing the view first and adding explicit keyboard selection
fixed both. Browser rechecks confirmed the changes in
[HotelMap.vue](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/frontend/src/components/HotelMap.vue).
[The evidence log](https://github.com/tmy5235/Expedia-Clone/blob/3e432bcb22d0cd24ae8e78538de1958deb6e8237/docs/assignment2-ai-evidence.md) links prompts to implementation
and verification details.
