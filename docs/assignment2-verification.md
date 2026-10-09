# Hotel Finder — verification

Historical Part 1 checkpoint. Counts, interface labels and screenshots below
record September 29, not the current Part 2 release. Current Part 2 results and
repeat instructions are in [RAG verification](rag-context.md).

Observed September 29, 2026, in America/New_York. Environment: Python 3.14.7,
Node 24.18.1, Leaflet 1.9.4. Tests use temporary SQLite databases and mocked
provider transport; normal accounts and bookings were not changed.

## Results

| Input/action | Expected | Observed |
| --- | --- | --- |
| Backend suite | Discovery, accounts, pricing, migration, CRUD and persistence pass | 117 passed; one existing Starlette TestClient deprecation warning |
| Frontend suite | API, request state, selection and booking regressions pass | 32 passed |
| Lint/build | No lint errors; production compilation succeeds | Both linters and Vite build passed |
| Live ZIP `16802` | Exact ZIP center and hotels within 5 km | State College, center 40.80317 / -77.86138; 20 hotel cards/markers and cap notice. Count is an observation, not a fixed test requirement. |
| List Enter / marker Space or Enter | Same selected hotel in both views | Scholar Hotel list selection and Hampton Inn marker selection synchronized the card, pin and popup |
| Invalid `123` | Validation without provider lookup | Five-digit feedback; old results removed |
| Simulated `00501` | Retain leading zero and honest fields | Center labeled SIMULATED TEST DATA; two fictional places, including missing name/address labels |
| Simulated `99999` | Successful empty response | No-hotels message with center/radius map |
| Simulated `00000` | Unresolved ZIP | ZIP-specific error; no stale hotels |
| Simulated `11111` / `22222` | Failure / rate-limit feedback | Distinct failure and try-later messages; neither becomes empty success |
| Edit query / late response | Clear old selection and ignore stale data | Browser and automated checks passed |
| Duplicate submit / timeout | One pending request and eventual recovery | Automated checks passed |
| Malformed fields / wrong ZIP / duplicates / radius | Reject mismatches or disclose omissions | Backend/frontend checks passed; wrong ZIP never triggers Places |
| Provider name containing `<text>` | Literal text, not HTML | Literal name in both card and popup |
| 390 px viewport | Readable stacked layout without overflow | Page and viewport both 390 px; keyboard selection and attribution remain available |
| Separate `/?demo=booking` page | Original account/history available | Existing session and saved history rendered; no mutations |
| Credentials | Key absent from tracked files and frontend build | `.env` ignored/untracked; configured key absent from built assets |

Six live discovery submissions were made across development and final review.
Fixture checks made no Geoapify calls. The final footer reads “Assignment 2.1 · IST
402”; the old booking-demo toggle is absent from the discovery homepage.

## Reproduce automated checks

From the repository root:

```bash
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm test && npm run lint && npm run build)
(cd frontend && npm ls leaflet --depth=0)
git diff --check
```

## Live browser check

Start both services using the [README](../README.md). Submit `16802`, observe
loading and the resolved location, then select a list card with Enter and a
different map marker with Space. Confirm the same hotel is selected in both views.
Inspect source attribution, the 5 km circle and result-limit notice. Submit `123`
and verify validation replaces the old results. Live coverage and ordering can change.

## Simulated browser checks

Start these on unused ports, in separate terminals:

```bash
# From backend/
EXPEDIA_DB_PATH=/tmp/expedia-discovery-browser-check.sqlite3 .venv/bin/python -m uvicorn tests.discovery_browser_server:app --host 127.0.0.1 --port 8001
```

```bash
# From frontend/
EXPEDIA_API_TARGET=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Open http://127.0.0.1:5174. The ZIP mappings in the table are fixtures, not claims
about real coverage. The dedicated server blocks live Geoapify transport; normal
OSM tiles still load. Stop only these two fixture processes afterward.

## Evidence and limitations

- [Homepage](screenshots/assignment2-final-home.png)
- [Live synchronized selection](screenshots/assignment2-final-results.png)
- [Mobile layout](screenshots/assignment2-final-mobile.png)

The early mockup is retained in the [research record](assignment2-research.md).
Intermediate screenshots were removed from the active evidence set after the
final views were captured.

Map initialization and marker Enter synchronization failed during development and
were corrected and rechecked; see [AI evidence](assignment2-ai-evidence.md).
No live quota was exhausted and no real tile outage was forced. Provider fields,
coverage and imagery vary. Discovery does not alter SQLite persistence; original
booking restart behavior was regression-tested with temporary databases rather
than by stopping the normal services. The existing TestClient warning remains.
