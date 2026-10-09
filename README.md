# Hotel Finder

Hotel Finder first checks locally saved hotels for a U.S. ZIP code, then searches
Geoapify only when local lookup succeeds with no matches. Results use a synchronized
list and map. Vue handles the interface, FastAPI handles validation and storage,
and Leaflet displays OpenStreetMap tiles.

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
- Add/Remove local hotels with database-backed saved status and ZIP associations.
- Ask about saved stays through a two-stage LLM assistant with checked read-only
  SQL, supporting records, and persistent conversation history.
- Saved results display dated, clearly labeled simulated classroom rates and room
  counts. Geoapify supplies no rates, ratings or availability; attribution remains visible.

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

Search runs only on submission. A local hit makes no Geoapify request. A successful
empty local lookup falls back to the frozen Part 1 endpoint, normally using two
provider requests: geocoding and Places. A local error stops the search and shows
feedback; it never triggers provider fallback. There is no automatic retry or pagination;
selecting hotels or moving the map makes no additional Places requests. Coverage
varies, and the 20-record limit is not an exhaustive inventory. Tile availability
is independent of hotel results.

The sample booking database is created at `backend/data/expedia.sqlite3` and seeded
once from `expedia-clone-data/`. Later starts preserve accounts and saved booking
changes. `EXPEDIA_DB_PATH` selects another database, such as a temporary test file.
Live discovery alone does not save hotels or record hotel-name searches. Explicit
Add/Remove actions change only the local-hotel storage, never Assignment 1 records.

Schema versions 3 and 4 add local-hotel tables for Assignment 2 Part 2. Startup migrates
existing databases transactionally without reseeding or changing Assignment 1
records. Fresh databases receive the same schema; repeated startup preserves it.

- `saved_hotels`: the API's `hotels[].place_id` maps unchanged to the unique
  `hotel_id` primary key. `name`, `address`, `latitude`, and `longitude` map to
  columns of the same names. Name and address may be NULL; coordinates are required
  and constrained to latitude −90…90 and longitude −180…180.
- `demo_hotel_nights`: one row per `(hotel_id, stay_date)`, with a foreign key to
  `saved_hotels`, a valid `YYYY-MM-DD` calendar date, and nonnegative integer
  `nightly_rate_cents` and `rooms_available`. Defaults are `10000` ($100.00) and `20`.
  These are **fictional classroom defaults**, not API prices or availability.

- `saved_search_locations`: the searched ZIP and its stored U.S. location/center,
  separate from the hotel's postal address. The first saved context for a ZIP is
  retained for later local lookups.
- `saved_hotel_zips`: a unique hotel/ZIP association with foreign keys to both
  records. One provider hotel can be associated with multiple searched ZIPs.

Saving creates five demo nights, **October 10–14, 2026 inclusive**, using the
database defaults. Repeated saves add only missing associations/nights and preserve
existing rates and room counts. Removing a hotel deletes it, all of its ZIP
associations and its demo nights in one transaction. Other hotels are preserved.
The local collection is shared by this classroom app; it is separate from signed-in
Assignment 1 bookings. Saved results represent only the saved subset, not all nearby hotels.

The original `GET /api/discovery/hotels?postcode=...` contract is unchanged.
New endpoints are:

| Endpoint | Purpose |
| --- | --- |
| `GET /api/local-hotels?postcode=00501` | Saved hotels, stored search center and dated demo nights; an empty list permits API fallback |
| `POST /api/local-hotels` | Save `{hotel: {place_id, name, address, latitude, longitude}, center: {postcode, country_code, locality, latitude, longitude}}` |
| `POST /api/local-hotels/status` | Resolve global saved IDs for `{place_ids: [...]}`, including hotels saved under another ZIP |
| `DELETE /api/local-hotels?hotel_id=...` | Atomically remove one provider hotel and its dependent local records |

No additional setup or dependencies are needed. See the
[workflow verification checkpoint](docs/assignment2-part2-local-workflow.md) and
the earlier [schema checkpoint](docs/assignment2-part2-schema.md).

When editing this database in DB Browser for SQLite, use **Write Changes** to
save edits (or **Revert Changes** to discard them) before using Add/Remove in the
app. Pending edits hold SQLite's write lock and block application mutations.
The app reports "Database is busy" in this situation. After releasing the lock,
retry the action; a failed removal leaves the hotel's related records intact.

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

- [Part 2 report](report.md)
- [Part 2 submission checklist](docs/assignment2-part2-submission-checklist.md)
- [Part 2 research and early design](docs/assignment2-rag-research.md)
- [RAG verification, evidence and recording instructions](docs/rag-context.md)
- [Part 1 research and early design](docs/assignment2-research.md)
- [Discovery API and MVC design](docs/assignment2-design.md)
- [AI development evidence](docs/assignment2-ai-evidence.md)
- [Selected prompts](prompts/README.md)

Source is separated into `backend/app/` and `frontend/src/`; tests live alongside
each application. `docs/` contains design and verification evidence. Development
status is recorded in `handoffs/current.md`. Secrets, dependencies, build output,
caches and local SQLite files are excluded from version control.

## Part 2.2 — saved-hotel assistant

The assistant below the discovery results uses **OpenAI** through the backend.
No new dependencies are required. In the existing project-root `.env`, add:

```dotenv
OPENAI_API_KEY=your-own-private-api-key
OPENAI_MODEL=gpt-4.1-mini
```

The classroom variable `OPEN_AI` is also accepted if `OPENAI_API_KEY` is absent.
Never put these values in Vite settings or commit `.env`. API credit/model access
is separate from a ChatGPT subscription. Restart FastAPI after configuration or
prompt changes. `GET /api/chat/status` reports only model/configuration status;
it does not make a paid call. The backend makes at most two model calls per question,
with no automatic retries. The student selected OpenAI and configured the key privately.

The first request includes `prompts/hotel-assistant.md`, its actual three-table
schema, the question and up to 12 prior user/answer messages. The model proposes
a parameterized SELECT. SQLite executes it on a separate read-only connection
with a default-deny authorizer, permitted tables/functions, a 0.5-second/200,000
VM-step work budget, and at most 30 rows. The backend independently checks each
returned hotel's ZIP, complete stay nights, available rooms and full integer-cent
total against the same database snapshot. Checkout is excluded; missing nights
are unknown. It then sends the original question and verified nightly records to
the model for a grounded answer. The assistant supports 1–14-night available-stay
comparisons; it does not book or edit hotels. Model interpretation and prose still
need review against the visible evidence.

Schema v5 adds only `chat_conversations` and `chat_messages`. Each turn saves the
prompt/hash, model/mode, user question, both request payloads, proposed/executed
SQL, retrieved rows, final answer or safe error. Conversation writes are separate
from the model's read-only query. Existing v1–v4 databases migrate without reseeding.
Like the local-hotel collection, chat history is shared by this local classroom
app, separate from Assignment 1 accounts. Do not put personal information in chat.
Only the three hotel tables are accessible to model-generated queries; account,
booking and conversation tables are denied. Keep this classroom app on localhost.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/chat/catalog` | Saved hotel counts, ZIPs and recorded dates for guided questions |
| `GET /api/chat/status` | Safe configuration, model and prompt version |
| `POST /api/chat` | `{question, conversation_id?: UUID}` → answer and retrieval evidence |
| `GET /api/chat/conversations` | 100 newest saved conversations |
| `GET /api/chat/conversations/{id}` | Last 500 saved trace steps in chronological order |

An empty collection now explains how to search and **Add to Local**. Saved ZIPs
and recorded nights appear above chat, and suggested-question buttons fill in
valid examples. Questions without any date in the user’s current/recent input
ask for clarification instead of copying dates from a prompt or assistant reply.
These local guidance responses make no model call; complete comparisons keep the
two-request RAG flow. Existing validation details remain in the evidence trace,
with plain-language feedback in the conversation.

Ask, for example: “Show the three cheapest saved hotels near ZIP 16803 with at
least one room for October 11, 2026.” For multiple nights specify check-in and
checkout. Expand **View supporting records & SQL** to inspect evidence.
Reload restores the latest conversation; the sidebar opens other saved exchanges.
No conversation state is persisted in browser storage.

See [RAG verification and recording instructions](docs/rag-context.md),
[research](docs/assignment2-rag-research.md), and the
[early mockup](docs/screenshots/assignment2-rag-early-mockup.svg).
