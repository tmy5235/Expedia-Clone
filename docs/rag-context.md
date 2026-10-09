# RAG context and verification — Part 2.2

Observation date: October 8, 2026, America/New_York. **Live OpenAI and mock verification complete. The source/evidence are published at assessed commit `dd495d1`. The student reports the recording complete; its accessible URL is still needed for the final report.**

## Reproduce deterministic verification

```bash
(cd backend && .venv/bin/python -m pytest -q)
(cd frontend && npm test && npm run lint && npm run build)
```

The [fixed JSON](evidence/assignment2-rag/fixed-hotels.json) is entirely fictional.
The isolated browser server seeds it only once, so restarting preserves local
removals and conversations. Use a new temporary file for a fresh run:

```bash
cd backend
EXPEDIA_DB_PATH=/tmp/expedia-rag-browser.sqlite3 .venv/bin/python -m uvicorn tests.rag_browser_server:app --host 127.0.0.1 --port 8001
```

```bash
cd frontend
EXPEDIA_API_TARGET=http://127.0.0.1:8001 npm run dev -- --host 127.0.0.1 --port 5174 --strictPort
```

Open http://127.0.0.1:5174. Ports must be free; never stop an unrelated process.
This server says **MOCK — no live model calls**, refuses live provider traffic,
and requires a `/tmp` database. Its response rules cover only the documented
fixture questions, not general language understanding. Never use this server as
live-model evidence. Normal startup is `app.main:app` on 8000, README frontend on 5173.

## Actual schema and JOINs

- `saved_hotels(hotel_id, name, address, latitude, longitude)` holds provider identities.
- `saved_hotel_zips(hotel_id, postcode)` joins `h.hotel_id=z.hotel_id` to select hotels saved from that ZIP search.
- `demo_hotel_nights(hotel_id, stay_date, nightly_rate_cents, rooms_available)` joins `h.hotel_id=n.hotel_id` to retrieve dated simulated rates and availability.

The query prompt is [hotel-assistant.md](../prompts/hotel-assistant.md), loaded at
startup. A SHA-256 prefix identifies its version in every trace step. Conversation
records retain the exact prompt and both outbound message payloads without keys.

## Trace example (MOCK)

Question: “Compare the cheapest saved hotels near 16803, checking in October 11
and out October 13, 2026.”

Browser conversation: `3f3f9ba3-dacb-43eb-a8d4-86667fc8367f` in the temporary
browser database. This ID is local evidence, not a remotely accessible resource.

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

Parameters: `postcode="16803"`, `check_in="2026-10-11"`, `check_out="2026-10-13"`.
The backend wraps the proposed query with `LIMIT 31` and rejects a 31st row,
then checks actual nightly records before augmenting the second request.

| Retrieved hotel | October 11 | October 12 | Complete stay | Availability |
| --- | --- | --- | --- | --- |
| Fictional Brook Hotel (`fixture-1`) | $90 | $90 | $180 | 20 each night |
| Fictional Pine Inn (`fixture-0`) | $80 | $120 | $200 | 20 each night |

Missing-night and sold-out fixtures are absent. October 13 is checkout and excluded.
The displayed mock answer recommends Brook first, gives $180/$200 totals and
each nightly price, minimum 20 rooms, and explicitly labels simulated course data.
[Answer screenshot](screenshots/assignment2-rag-mock-answer.jpg).
The full exported trace is [mock-browser-traces.json](evidence/assignment2-rag/mock-browser-traces.json).

## Expected versus observed

| Check | Expected | Observed |
| --- | --- | --- |
| Existing backend regression | Preserve discovery, accounts, pricing, bookings, local storage | 182 existing tests passed after integration |
| New RAG tests | Two model stages, checked retrieval, persistent traces | 46 RAG tests; 228 total backend tests passed |
| Multi-night fixture | Brook $180 before Pine $200, missing/sold-out excluded | Matched backend tests and browser answer |
| Single night October 11 | Pine $80; October 12 excluded | Automated test passed |
| Request through October 16 | Missing October 15 prevents availability | Empty records in automated test |
| ZIP `00501` | Leading zero preserved, no invented alternatives | Empty records and no-match answer in tests and browser |
| Model proposes DELETE/private-table read/PRAGMA/extension | Reject before answer, preserve records, save error | Temporary-database attack tests and browser DELETE rejection passed; no second model request |
| Inaccurate total or incomplete returned stay | Reject rather than present as available | Tests passed |
| Expensive query / excess rows | Bounded retrieval failure | Tests passed |
| Provider 401/403/429/500, malformed response, timeout | Safe specific error, no credentials exposed | Tests passed; revised exception type fixed swallowed quota/auth status |
| Reload/restart | Same conversation trace and hotel records | Automated and both-service browser restart passed; 25 stored trace steps matched exactly |
| Keyboard | Card Enter, marker Space and Send Enter work | Browser selected Brook consistently and submitted the multi-night question |
| Pending | Disabled duplicate send and visible working feedback | Observed in browser |
| Frontend | Tests, lint, build | 47 tests and both linters/build passed |
| Live model | Two successful real model calls and grounded answer | VERIFIED — real OpenAI multi-night, follow-up and no-match calls; see live evidence below |

Browser mobile check: 390 px viewport/document width, no horizontal overflow;
[mobile screenshot](screenshots/assignment2-rag-mock-mobile.jpg). Simulated 429
and DELETE both produced saved failures without a fabricated assistant answer.
Restart preserved 4 hotels, 19 nightly records and all 25 trace records.

## Live OpenAI verification

The privately configured key works with `gpt-4.1-mini`. The live test used the first
four hotel places from [the earlier captured API response](evidence/assignment2-part2/api-response.json),
saved in an isolated database under ZIP 16802. Nightly data was deliberately
simulated: Scholar $80/$120 for Oct 11/12, Hotel State College $90/$90, Nittany
missing Oct 12, and Hyatt zero rooms Oct 12. Normal application data was unchanged.

- Multi-night Oct 11–13: **$180 and $200**, correct nights and available rooms.
- Follow-up just Oct 12: **$90 and $120**, inherited ZIP 16802 and Oct 13 checkout.
- No-match Oct 20: empty rows; natural-language explanation without invented hotels.
- Frontend displayed the persisted real answers after reopening the backend.

[Complete live traces](evidence/assignment2-rag/live-verified-trace.json) and
[live screenshot](screenshots/assignment2-rag-live-answer.jpg). The trace preserves
initial failures. Separate stage prompts corrected SQL appearing as the answer;
a clearer single-night contract corrected missing checkout; explicit cursor
closure corrected a read lock that prevented recording a rejected projection.
All three fixes have regression coverage. A verified single-night nightly-rate
column is now accepted even if the model omits the `total_cents` alias.

The no-match live answer omitted the word “simulated”; it gave no prices or offers,
and the frontend's permanent simulated-data label remained visible. The initial
verification script's literal-word assertion failed on that harmless omission;
manual comparison confirmed correct empty-data behavior. This is documented
rather than hidden or repeatedly querying the provider for preferred wording.

## Student recording and final verification

See the [submission checklist](assignment2-part2-submission-checklist.md). In the
current interface, expand **View supporting records & SQL**. For mock failure
checks, include dates so the date-guidance preflight permits the fixture call:
`delete saved hotels near 16803 for October 11–13, 2026` or
`rate limit near 16803 for October 11–13, 2026`. These phrases trigger the
deterministic mock; they do not describe how the live model will respond.

1. Privately configure the chosen provider key and model in `.env`; restart the normal backend. Confirm `/api/chat/status` has `configured: true` and `mode: live OpenAI`. Do not record `.env` or credential screens.
2. Use existing saved hotels, or search a ZIP and Add to Local. Record actual ZIP and observation date. Inspect the dated simulated rows and preserve any manually edited values.
3. Ask the single-night example using a ZIP with saved hotels; then compare a two-night stay and ask “What about October 12?” Expand the trace to show question, first request, proposed/executed SQL, parameters, retrieved rows, second request and displayed answer. Compare each price/night/count with SQLite.
4. Ask about a date without records (for default data, October 20, 2026). Verify no-match/insufficient-data feedback rather than invented availability.
5. Demonstrate blocked DELETE using the explicitly labeled fixture server (“delete saved hotels near 16803 for October 11–13, 2026”), never by writing to the normal database. Show the saved error and unchanged row counts.
6. Refresh and restart both services with the same database. Reload the conversation and show the same timestamps/steps. Verify local Add/Remove changes remain persisted.
7. Record a short narrated screen video. Explain retrieval versus answer generation, simulated rates, checkout exclusion, no-match behavior and mock/live distinctions. Upload it somewhere the instructor can open without an access request.
8. Add the live conversation evidence, recording URL, assessed pushed commit, and verified AI model identity to `report.md`. Check every report link from the instructor's perspective. Upload that single Markdown report to Canvas.

Read-only SQLite inspection:

```sql
SELECT conversation_id, title, created_at FROM chat_conversations ORDER BY created_at DESC;
SELECT message_id, conversation_id, timestamp, role, stage, content, prompt_version
FROM chat_messages WHERE conversation_id = 'YOUR-CONVERSATION-ID' ORDER BY message_id;
PRAGMA foreign_key_check;
PRAGMA user_version; -- 5
```

## Practical limits

Only available-stay comparisons over saved hotels are supported; no occupancy
forecast, reservations, reviews or amenities. Max 30 hotels and 14 nights per
request. Model prose and intent interpretation are probabilistic; the visible
trace enables review but does not prove every answer claim is correct. Query
validation guarantees table access and data integrity, not perfect intent parsing.
History is shared locally, newest 100 conversations/last 500 steps displayed;
older rows remain in SQLite. Prompts/results go to the configured provider;
accounts/bookings/credentials are excluded. One existing Starlette warning remains.

## Guided questions and readability correction

Student testing found an empty saved collection, a question without dates that
received an invented date, and a general list request that exposed a SQL-column
error. Corrected by local preflight guidance (no paid model calls), a read-only
`/api/chat/catalog` endpoint, examples derived from actual saved ZIPs/recorded
nights, user-friendly error messages with technical details retained in the trace,
and cleaner typography/paragraph/list rendering. The normal collection was left
unchanged. Existing saved chat history remains intact.

Expected/observed: empty collection gives Add to Local steps; date-free request
asks for dates without a model request; assistant-guessed dates are not accepted
as user context. Backend tests cover all three. Browser on the isolated live
fixture: a date-free request asked for dates; **Find the cheapest** filled ZIP
16802 / Oct 10, 2026; real OpenAI returned Scholar $80, Hotel State College $90,
and Hyatt $100 with 20 simulated rooms each, matching the retrieved records.
Keyboard Send and mobile 390 px width passed; no horizontal overflow.

[Live guided-question trace](evidence/assignment2-rag/guided-question-live.json),
[updated empty guidance](screenshots/assignment2-rag-guidance.jpg),
[updated answer](screenshots/assignment2-rag-guided-answer.jpg).
Final checks: 221 backend tests, 47 frontend tests, lint and production build pass.

## Product wording revision

At the student's request, removed class/assignment references from headings,
helper text, save/remove notices, the booking page and new chatbot guidance.
Replaced the repeated classroom labels and prominent badge with brief
“Rates and availability are simulated” disclosures near the relevant data.
Prompt v5 requests travel-app language without course terminology; historical
conversation rows and original evidence remain unchanged. Use New conversation
for a fresh view. Raw technical traces remain available for assessment.

Expected: product-oriented interface, no classroom references in current static
copy, clear simulated-rate disclosure, unchanged retrieval/storage behavior.
Observed: browser verified the fresh conversation and booking pages; 221 backend
and 47 frontend tests, both linters and production build passed. The existing
Starlette deprecation warning remains. No live model call was made for this
wording-only revision, so new model prose remains probabilistic.
[Updated interface](screenshots/assignment2-product-copy.jpg).

## Suggested-question failures and date recognition fix

The student's three suggested questions failed despite valid ZIPs and dates.
The live model included `rooms_available` or `available_rooms` alongside IDs and
totals; the old exact-column validator rejected them. It also rejected harmless
column reordering. Optional room counts now pass only when they equal the actual
minimum over the requested nights; totals, complete-night coverage, ZIP association,
allowed tables/functions and read-only/work/result limits remain enforced.
Unknown columns and invented counts still fail. Prompt v6 documents the contract.

The date-presence preflight missed `10-20-26` and `10-20-2026`. Both now reach the
LLM for interpretation and ISO date validation. They do not create availability:
October 20–22 correctly returns no matches in the default dataset.

Seven regression cases added: optional room aliases and false counts, reordered
single-night budget columns, and four numeric date forms. Five failed before the
fix; all seven now pass. Latest complete checks: **228 backend tests (46 RAG),
47 frontend tests, lint and build passed**. Existing Starlette warning remains.

Four real OpenAI checks used only entirely fictional repository fixtures in a
temporary database; no normal saved hotels or conversation rows were changed.
Automatic review declined a proposed copied-collection live test; the performed
test instead used fictional fixtures and was approved.

| Question | Expected | Observed |
| --- | --- | --- |
| Suggested two-night comparison, 16803 Oct 10–12 | Three cheapest totals $160/$180/$200, 20 rooms | Matched records and live answer |
| Suggested $150 budget, Oct 10 | Four hotels $80/$90/$100/$100 | Matched |
| Suggested three cheapest, Oct 10 | $80/$90/$100 | Matched |
| `10-20-26 check-in, 10-22-26 check-out 16803` | Two model requests, empty records, no-match explanation | Matched; no repeated date clarification |

[Complete live traces](evidence/assignment2-rag/room-projection-live.json) preserve
both model requests, SQL, retrieved records and answers. Browser inspection after
starting the services with this same temporary database showed the successful
comparison and no-match answer; both remained accessible after refresh.
[Browser evidence](screenshots/assignment2-room-projection-fix.jpg). Temporary
services were stopped after verification; normal app remains on 8000/5173.
