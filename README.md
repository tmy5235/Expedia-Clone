# Hotel Finder

Hotel Finder searches hotel locations near a U.S. ZIP code and displays them in
a synchronized list and map. Vue handles the interface, FastAPI handles Geoapify
requests and validation, and Leaflet displays OpenStreetMap tiles.

A separate fictional booking demo at `/?demo=booking` provides account login,
hotel-name search, personalized sample prices, and persistent booking history.
Live hotel locations are independent of those sample stays and cannot be booked.

## Features

- Five-digit U.S. ZIP input, including leading zeros; the returned location must
  match the requested ZIP before a hotel search runs.
- Hotels within 5 km of the returned ZIP point, with one page of up to 20 records.
  The center is not the user's location or the entire ZIP boundary.
- Shared selection between numbered hotel cards and map markers, including
  Enter/Space keyboard controls and a responsive layout.
- Separate loading, invalid input, unresolved ZIP, empty, failure and rate-limit
  feedback. Missing hotel names and addresses are labeled honestly.
- Visible provider attribution; no invented rates, ratings or availability.

## Setup

Tested with Python 3.14.7 and Node 24.18.1. Python 3.11+ is needed for the backend's
type features; the frontend declares Node `^22.18.0 || >=24.12.0`.

From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Create a project-root `.env` beside `backend/` and `frontend/`:

```dotenv
GEOAPIFY_API_KEY=your-own-local-key
```

The backend loads this file using an explicit path. Process environment values
have priority. Keep the file untracked and never put this key in a `VITE_`
variable. Restart FastAPI after changing the key. `GET /api/health` reports only
whether it is configured; that check does not contact Geoapify.

Start the backend:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, start the frontend:

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173. Vite proxies `/api` to port 8000. Set
`EXPEDIA_API_TARGET` to use a different backend for isolated checks.
Leaflet 1.9.4 is pinned in the frontend manifests. OSM raster tiles need no key.

## Data and request behavior

Search runs only on submission. A resolved search normally uses two provider
requests: geocoding and Places. There is no automatic retry or pagination;
selecting hotels or moving the map makes no additional Places requests. Coverage
varies, and the 20-record limit is not an exhaustive inventory. Tile availability
is independent of hotel results.

The sample booking database is created at `backend/data/expedia.sqlite3` and seeded
once from `expedia-clone-data/`. Later starts preserve accounts and saved booking
changes. `EXPEDIA_DB_PATH` selects another database, such as a temporary test file.
Live discovery does not change the booking database or record hotel-name searches.

## Fictional booking demo

Open http://127.0.0.1:5173/?demo=booking. Sample users `traveler1` through
`traveler6` use the fictional password `classroom-demo`. Accounts and sessions are
managed by the backend. Each account can create, read, cancel and delete only its
own bookings. Passwords are stored as readable text for the local demo; use only
fictional credentials.

For the same signed-in user, normalized hotel-name query and day in
`America/New_York`, searches 1–3 return the base rate; search 4 onward returns base
× 1.20 once. The accepted total is saved with the booking. Anonymous searches use
base rates. See [booking design](docs/design.md) for migration and pricing details.

The demo also includes a [ZIP-coordinate lookup](docs/zip-lookup.md) that displays
the verified ZIP, country, locality and coordinates without requesting hotels.

## Verification

```bash
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm test && npm run lint && npm run build)
```

Automated tests mock provider requests and use temporary databases. Browser
verification and simulated-provider instructions are in the
[discovery verification guide](docs/assignment2-verification.md). Original account,
pricing and persistence checks are in the [booking verification guide](docs/verification.md).

## Documentation

- [App report](report.md)
- [Research and early design](docs/assignment2-research.md)
- [Discovery API and MVC design](docs/assignment2-design.md)
- [AI development evidence](docs/assignment2-ai-evidence.md)
- [Selected prompts](prompts/README.md)

Source is separated into `backend/app/` and `frontend/src/`; tests live alongside
each application. `docs/` contains design and verification evidence. Development
status is recorded in `handoffs/current.md`. Secrets, dependencies, build output,
caches and local SQLite files are excluded from version control.
