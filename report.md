# Assignment 2.2 — Business Intelligence with RAG

Implementation and verification completed October 8, 2026, Eastern. The app
extends persistent local hotel storage with a two-stage SQL-based RAG assistant.
Live provider checks and deterministic mock checks are labeled separately.

## Project access and setup

Repository: [tmy5235/Expedia-Clone](https://github.com/tmy5235/Expedia-Clone).
Working branch: `rag_integration`. Assessed application/evidence commit:
[`dd495d1`](https://github.com/tmy5235/Expedia-Clone/commit/dd495d1bc8b979694eac94af5a9b32b65f4bed9c).
The branch includes the local-storage foundation and RAG extension. The
[Part 1 report](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/assignment2-part1-report.md) is retained separately.

**Demo recording:** See the accompanying Canvas submission comment for the
student’s screen-recorded demonstration.

Use the existing dependencies: Python 3.11+ (tested 3.14.7), Node `^22.18.0 || >=24.12.0`
(tested 24.18.1). No dependencies were added for the chatbot. Existing HTTPX
0.28.1, FastAPI 0.141.1 and Pydantic 2.13.4 were checked before implementation.

Fresh checkout setup:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Privately create the ignored project-root `.env`:

```dotenv
GEOAPIFY_API_KEY=your-own-private-key
OPENAI_API_KEY=your-own-private-key
OPENAI_MODEL=gpt-4.1-mini
```

OpenAI is configured and verified with the student’s privately supplied API key,
following the in-class activity. The instructor variable
`OPEN_AI` is accepted as a fallback. No credential is included in frontend code,
Vite configuration, this report or the evidence. Restart after changing `.env`
or `prompts/hotel-assistant.md`.

In separate terminals:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173. Search a ZIP and Add to Local, then use **Ask about saved
hotels**. `GET /api/chat/status` reports model and configured/not-configured without
exposing credentials or making a paid call. The existing database remains at
`backend/data/expedia.sqlite3`; `EXPEDIA_DB_PATH` selects a separate test database.
[README](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/README.md) documents the full API, configuration and data behavior.

## Research and early design

[Part 2 research notes](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/assignment2-rag-research.md) were written before chatbot
source implementation, building on the [Part 1 research](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/assignment2-research.md).

| Source | Useful pattern or limitation | Adopted decision |
| --- | --- | --- |
| [Booking.com AI Trip Planner](https://news.booking.com/bookingcom-launches-new-ai-trip-planner-to-enhance-travel-planning-experience) | Follow-up questions refine hotel choices; its live booking context differs from our saved classroom dataset | Conversational input and saved history, clear simulated-data label, no reservation action |
| [OpenAI Chat Completions](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) | Role-based input and JSON output support a query proposal; output still needs validation | Two backend requests, parsed JSON proposal, independent SQL and data checks |
| [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini) | Documents Chat Completions/structured-output support; account access is not established by documentation | Configurable model; verify real access separately |
| [Python sqlite3](https://docs.python.org/3/library/sqlite3.html) / [SQLite authorizer](https://www.sqlite.org/c3ref/set_authorizer.html) | Engine authorization checks statements during preparation | Read-only connection, default-deny authorizer, work/result limits, separate history writes |

![Early chatbot mockup, prepared before source implementation](https://raw.githubusercontent.com/tmy5235/Expedia-Clone/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/screenshots/assignment2-rag-early-mockup.svg)

The mockup established a saved-conversation sidebar, composer, answer area,
retrieval disclosure, and loading/no-match/error states. The final implementation
places this panel beneath existing discovery results, stacks it on mobile, and
uses native buttons/disclosures for keyboard access. It adds a **Reload**
control and shows prompt/version details within nested disclosures for assessment.

## Implemented workflow and MVC

1. Vue sends the question and optional conversation ID to FastAPI.
2. The controller sends the prompt file, actual schema/query rules, recent context
   and question to OpenAI. The model proposes SQL and bound parameters.
3. The Model opens SQLite in read-only mode with `query_only`, rejects everything
   except allowed reads/functions, and bounds query work and results. Allowed
   tables are only `saved_hotels`, `saved_hotel_zips`, and `demo_hotel_nights`.
4. It checks each result against actual ZIP associations and dated records in the
   same snapshot: complete nights, positive rooms, and correct total cents.
5. The controller sends the original question and verified records to the model
   in a second request, requiring an answer supported by those records.
6. Vue displays the answer and the inspectable trace. SQLite stores each stage as
   it occurs, including safe failures. Refresh/restart retrieves the saved history.

`h.hotel_id=z.hotel_id` links a place to its searched ZIP; `h.hotel_id=n.hotel_id`
links the place to nightly rates/rooms. Missing nights mean unknown availability;
checkout is excluded. Multi-night results use the full stay sum. The backend
supports 1–14 nights and at most 30 matching hotels, with a 0.5-second/200,000
SQLite VM-step work budget. Remote models never connect to SQLite.

The existing Model owns additive schema v5 migration, hotel persistence and
conversation storage. Controllers own LLM calls, prompts, validation and error
translation. Vue handles input, request feedback, history selection and display.
[Implementation](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/backend/app/controllers/chat.py), [read-only Model](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/backend/app/chat_store.py),
[prompt](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/prompts/hotel-assistant.md), [Vue panel](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/frontend/src/components/HotelAssistant.vue).

The local-storage foundation retains Add/Remove Local, deduplication, ZIP context,
local-first lookup and dated simulated rates. Part 1 discovery contracts/list/map
and Assignment 1 account/pricing/booking behavior remain covered by regressions.
Migration never reseeds an existing database. Normal application data was not
used for test mutations. Existing storage evidence remains in the
[local workflow checkpoint](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/assignment2-part2-local-workflow.md).

## Demonstration evidence

**Live provider workflow verified with `gpt-4.1-mini`.** The student configured the
API key privately. Real first/second model requests returned the expected multi-night,
follow-up single-night and no-match results. These checks used an isolated database
with four public places from the [previously captured Geoapify response](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/evidence/assignment2-part2/api-response.json),
ZIP **16802**, and deliberately simulated course nightly records. No new Geoapify
request was made and the normal application database was unchanged.

| Real model question | Retrieved records and displayed result |
| --- | --- |
| Three cheapest available stays, Oct 11–13, 2026 near 16802 | Hotel State College $90 + $90 = **$180**; Scholar Hotel $80 + $120 = **$200**. Missing-night Nittany Lion Inn and sold-out Hyatt Place are excluded. |
| “What about just the night of October 12, 2026?” | ZIP retained from history; checkout Oct 13; Hotel State College **$90**, Scholar Hotel **$120**, 20 simulated rooms each. |
| “Now check the night of October 20, 2026, in that same ZIP.” | Empty retrieval; answer explains no saved rates/available rooms for that date and suggests changing dates/ZIP or saving more hotels. No invented alternatives. |

[Full live question → proposed/executed SQL → records → second request → answer trace](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/evidence/assignment2-rag/live-verified-trace.json).
The frontend loaded and displayed the real saved answers after a backend restart.
The live trace also preserves failed attempts used to improve the implementation;
HTTP 200 alone was not counted as evidence of a correct answer.

![Real OpenAI answer using explicitly simulated rates](https://raw.githubusercontent.com/tmy5235/Expedia-Clone/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/screenshots/assignment2-rag-live-answer.jpg)

Live corrections: separate query/answer system instructions after the first model
returned SQL for both stages; explicitly require single-night checkout; close active
SQLite cursors before saving query-rejection errors; accept an unaliased nightly-rate
column only for a verified one-night stay. New tests cover stage separation,
wrong-stage rejection, cursor cleanup and safe single-night handling.

The reproducible **MOCK** browser run used ZIP `16803` on October 8, 2026 Eastern,
with [fixed fictional JSON](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/evidence/assignment2-rag/fixed-hotels.json) and
`/tmp/expedia-rag-browser.sqlite3`. No live Geoapify search or live model call was
made in this run. The recorded mock answer and trace explicitly identify mock output.

Question: “Compare the cheapest saved hotels near 16803, checking in October 11
and out October 13, 2026.”

Conversation ID: `3f3f9ba3-dacb-43eb-a8d4-86667fc8367f`.

Proposed SQL:

```sql
SELECT h.hotel_id, SUM(n.nightly_rate_cents) AS total_cents
FROM saved_hotels h JOIN saved_hotel_zips z ON h.hotel_id=z.hotel_id
JOIN demo_hotel_nights n ON h.hotel_id=n.hotel_id
WHERE z.postcode=:postcode
  AND n.stay_date>=:check_in AND n.stay_date<:check_out
GROUP BY h.hotel_id
HAVING COUNT(*)=julianday(:check_out)-julianday(:check_in)
  AND MIN(n.rooms_available)>=1
ORDER BY total_cents, h.hotel_id LIMIT 3
```

Parameters: `16803`, `2026-10-11`, `2026-10-13` respectively. Execution uses an
outer 31-row limit and rejects a 31st result rather than silently truncating it.

| Retrieved record | Nightly records | Total | Rooms |
| --- | --- | --- | --- |
| `fixture-1`, Fictional Brook Hotel | Oct 11 $90; Oct 12 $90 | $180 | 20 on each night |
| `fixture-0`, Fictional Pine Inn | Oct 11 $80; Oct 12 $120 | $200 | 20 on each night |

Displayed mock answer: Brook is first at $180 for two nights; Pine is $200. It
lists those nightly prices, minimum 20 rooms, checkout exclusion and simulated
course data. Missing-night and sold-out hotels are excluded. The second request
contains the original question plus those verified nightly records.

![Mock answer; not live model evidence](https://raw.githubusercontent.com/tmy5235/Expedia-Clone/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/screenshots/assignment2-rag-mock-answer.jpg)

[Full question/SQL/results/request/answer trace](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/evidence/assignment2-rag/mock-browser-traces.json)
and [detailed reproduction/recording instructions](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/rag-context.md).

## Expected versus observed verification

| Input/action | Expected | Observed |
| --- | --- | --- |
| Backend regression + new RAG suite | Preserve original behavior and exercise retrieval/history/errors | **228 passed**, including 46 RAG tests |
| Frontend tests, lint, build | Functional request states and buildable Vue | **47 passed**, Oxlint/ESLint and production build passed |
| October 11–13 fixture question | Complete-night totals $180/$200; checkout excluded | Exact match in tests, browser answer and trace |
| Single night October 11 | Pine $80, October 12 not charged | Passed automated test |
| Stay through October 16 | Missing October 15 makes stay unavailable | Empty retrieved records |
| ZIP `00501` | Preserve leading zero; explain no matches | Browser and tests returned no-match feedback without invented hotels |
| Mock model DELETE | Block before execution; no answer fabricated; save error | HTTP 422, visible saved error, 4 hotel/19 nightly rows unchanged |
| Private tables, PRAGMA, ATTACH, extension/file functions, multiple statements | No private reads or writes | Attack fixtures rejected; data snapshots unchanged |
| Wrong total, wrong ZIP, incomplete/sold-out stay | Reject misleading proposal | Tests passed |
| Excess rows and expensive query | Stop with safe bounded-query error | Tests passed |
| Simulated model 429 | Useful retryable error, no quota exhaustion | Browser showed mock rate-limit error and preserved failed attempt |
| Credentials/timeout/malformed model reply | Safe failure without key disclosure | Mock HTTP tests passed; corrected error-class bug |
| Card Enter / map Space | Shared selection remains synchronized | Brook selected in both views |
| Send with keyboard | Pending feedback, disabled duplicate controls, eventual answer | Observed |
| Browser refresh + restart both services | Identical saved traces, preserved hotel data | 25 trace rows matched byte-for-byte fields; 4 hotels/19 nights remained; no FK violations |
| Mobile 390 px | Usable composer/history without horizontal overflow | Document and viewport widths both 390; [screenshot](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/screenshots/assignment2-rag-mock-mobile.jpg) |
| Live-model successful/no-match exchange | Real proposed SQL and grounded second reply | **Verified with real OpenAI calls; captured public places and simulated rates** |

Repeat automated checks:

```bash
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm test && npm run lint && npm run build)
```

The [verification guide](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/rag-context.md) includes temporary-server commands,
fixed fixture details and read-only SQLite queries. One existing third-party
Starlette TestClient deprecation warning remains; no dependency change was made.

Limitations: shared local classroom history, last 500 steps displayed per
conversation, newest 100 conversations listed, only saved available-stay
comparisons. Model interpretation/prose is probabilistic; SQL isolation and
nightly verification do not prove perfect interpretation of every budget or
preference. Review live answers against the displayed trace. No reservations,
real hotel rates, occupancy forecasts, reviews or amenities are inferred.

## AI disclosure and evidence log

OpenAI Codex desktop with **GPT-6 Astra** assisted with requirement analysis, official documentation
research, SVG mockup, Python/Vue implementation, tests, browser checks and this
report. The student confirmed GPT-6 Astra as the development model. Prior Part 1 disclosure is retained in
its archived report. No subagents or image-generation models were used.

The application uses `gpt-4.1-mini`; real provider calls were made during this
checkpoint and saved separately from mocked evidence. `fixture-model-no-network` is a deterministic Python mock, not
an LLM. Do not confuse it with the development assistant's model.

| Selected prompt/instruction | Code, decision or evidence |
| --- | --- |
| “continue this project to Part 2.2 … Start working on the requirements … let me know when you need me” | Preserve local-storage foundation; add full two-stage workflow on `rag_integration` |
| Assignment: “User question → LLM proposes SQL … validates and executes a read-only local query … sent to the LLM again” | [Controller](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/backend/app/controllers/chat.py), [Model](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/backend/app/chat_store.py), [prompt](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/prompts/hotel-assistant.md) |
| In-class activity: “Save the trace as each step happens” | Schema v5 messages with role/stage/timestamp, prompt hash, both request payloads and restart checks |
| Assignment: “checkout is excluded and missing nights must not be treated as available” | Independent nightly validation and $180/$200/missing-night fixtures in [tests](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/backend/tests/test_chat.py) |
| First implementation used `ChatError(ValueError)` | Failed 401/403/429 tests showed the broad parse-error handler swallowed intended statuses. Changed it to `Exception`; reran targeted and complete suites successfully |
| First live response returned SQL instead of prose; a follow-up omitted checkout and another proposal exposed a retained read lock | Separated stage instructions, clarified the date contract, closed active cursors before error persistence, and added regression coverage. Retained failed and corrected live traces for disclosure. |
| Row-bound fixture initially used an unused cross-join table | SQLite authorization rejected it before the intended row-bound assertion. Revised the fixture to reference the approved ZIP column; independently verified the 31st-row rejection |

## Usability correction after student testing

The student's empty collection and date-free questions exposed unclear guidance.
The interface now shows how to save hotels, lists actual saved ZIPs/nights, and
fills complete questions through three suggestion buttons. Empty collections and
missing-date questions receive local guidance without model requests. A prior
assistant guess cannot supply an absent user date. Technical validation evidence
remains inspectable while errors use plain language. Typography, paragraph/list
spacing and long conversation titles were simplified.

Browser verification with the captured-place fixture and real OpenAI:
**Find the cheapest** filled ZIP 16802 / Oct 10, 2026 and returned the verified
$80/$90/$100 options; keyboard submission and 390 px mobile layout passed.
[Guided live trace](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/evidence/assignment2-rag/guided-question-live.json) and
[updated layout](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/screenshots/assignment2-rag-guided-answer.jpg).

The final interface uses travel-app language and concise simulated-rate disclosures.
Earlier screenshots/traces preserve their original wording. The current prompt
retains the same data limitations while avoiding classroom language in new answers.
[Current interface](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/screenshots/assignment2-product-copy.jpg).

## Suggested-question reliability correction

Student testing revealed that valid suggested questions failed when the model
selected room counts in addition to IDs/totals. The validator now accepts the two
room-count aliases and different column ordering, independently checks those
counts against every requested night, and retains all read-only and correctness
checks. Numeric dates such as `10-20-26` now reach the model instead of repeatedly
triggering date guidance. Prompt v6 documents the allowed output.

Seven added regression cases pass; the full suite now has 228 backend tests
(46 RAG), with 47 frontend tests, lint/build passing. Four real model checks on
entirely fictional temporary data passed the three suggested questions plus the
numeric-date no-match case. No normal hotel/history records were modified.
[Expected/observed and browser evidence](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/rag-context.md#suggested-question-failures-and-date-recognition-fix),
[complete live traces](https://github.com/tmy5235/Expedia-Clone/blob/dd495d1bc8b979694eac94af5a9b32b65f4bed9c/docs/evidence/assignment2-rag/room-projection-live.json).

## Submission artifacts

The repository includes the source, startup instructions, early mockup, research,
fixed JSON, live/mock traces, and expected-versus-observed verification linked
above. The screen recording accompanies this report in the Canvas submission
comment. All source and evidence links above are pinned to the assessed
application commit; later documentation-only commits do not change that code.
