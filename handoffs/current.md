# Current Handoff

## Publication complete; recording URL needed

Published branch rag_integration to origin. Assessed application/evidence commit:
`dd495d1bc8b979694eac94af5a9b32b65f4bed9c`. Report has permanent GitHub source
links and raw image links. Credential and prohibited-file scans passed.
User reports recording complete but has not supplied a URL or local path; async
question is pending. Insert/verify its accessible link before Canvas upload.
Do not claim the recording was reviewed or the Canvas submission was completed.
No source changes since last 228 backend/47 frontend/lint/build pass; this turn
prepared publication and documentation only. Normal app stays running.

## Submission finalization in progress

User reports recording complete and authorized finalizing the submission. Awaiting
its instructor-accessible URL; no recording has been reviewed in this turn.
Preparing assessed commit, publication and pinned links. Code last verified with
228 backend tests (46 RAG), 47 frontend tests, lint/build and four live fixture
checks; no application code changed since. Public repository returned HTTP200.
All local Markdown links and publishable-file credential/ignored-file checks pass.

## Latest: suggested-question failures corrected

Actual saved traces identified overly strict output projection (model included
rooms_available / available_rooms). Accept and independently validate these
counts against full-stay minimum; accept column reordering. No weakening of SQL
authorization, total/ZIP/night validation or bounded read-only execution.
Date preflight now recognizes hyphenated U.S. numeric dates such as 10-20-26.
Prompt v6. Seven added cases; 228 backend tests (46 RAG), 47 frontend tests,
lint/build pass. Four live OpenAI fixture-only checks passed all suggested
questions and numeric-date no-match; browser history and refresh verified.
Evidence: docs/evidence/assignment2-rag/room-projection-live.json.
Normal app autoreloads the fix; normal hotels and chat history untouched. At
diagnosis user had 3 saved hotels associated with ZIP16803, nights Oct10–14.
Older summaries below are historical checkpoints.

## Latest app restart

Restarted both normal services at the user’s request. Backend session `44366`
(reloader PID 86225), frontend session `5894`; ports 8000/5173. Health reports OK,
frontend returns HTTP 200, and proxied chat status confirms configured live OpenAI
with gpt-4.1-mini and prompt version `73f9faccd8fd434a`. Same normal database;
services intentionally left running. These session IDs supersede older entries.

## Product wording revision — latest

- Removed visible course/assignment references, repeated classroom labels, prominent
  simulated-data badge and technical model footer. Kept brief simulated-rate
  disclosures required by the assignment near comparisons and saved rates.
- Updated save/remove feedback, backend preflight guidance and prompt v5. Existing
  saved responses and raw evidence are preserved; New conversation clears the view.
- Reran 221 backend tests, 47 frontend tests, lint/build: passed. Verified fresh
  conversation and original booking-page wording in the browser. No new live
  LLM call for the copy-only change. App stays running on 8000/5173.
- Report and verification notes include current wording and screenshot.

## Active submission status — October 8, 2026

Part 2 implementation and latest verification are complete: 221 backend tests
(39 RAG), 47 frontend tests, lint/build, isolated live and mock browser checks.
Application model is gpt-4.1-mini; development model is GPT-6 Astra. Normal app
was left running on 8000/5173. No dependencies added; work remains uncommitted.

Documentation audit updated the report, setup/frontend guides, selected prompts,
AI evidence, mock reproduction and historical checkpoint labels. Remaining:
student recording URL, reviewed publication/assessed commit, permanent accessible
artifact links, and Canvas upload. See
[submission checklist](../docs/assignment2-part2-submission-checklist.md).
Current assistant compares saved available stays using ZIP/date context; broader
all-hotel inventory queries were discussed but have not been implemented.

The entries below are chronological development checkpoints. Their older test
counts, provider blockers and Part 1 video instructions are historical; use the
active status above and current report for submission.

## Guided chatbot and typography correction

- User reported unsuccessful questions and crowded text. Normal collection was empty; saved trace also showed an invented date on a date-free question and a raw SQL projection error. No normal hotels or conversations were removed/changed during diagnosis.
- Added `/api/chat/catalog`, visible collection/recorded-date context, empty-state Add to Local steps and questions populated from saved ZIPs/dates. Add/Remove updates refresh context. Local guidance skips model calls for empty collections and missing user dates; assistant guesses do not count as user date context. SQL diagnostics remain in trace while error messages are readable.
- Simplified typography/spacing, clamped sidebar titles, rendered answers as safe text paragraphs/lists, removed duplicate errors, and restored composer focus after send. Prompt v4 requests concise answers.
- 221 backend tests (39 RAG), 47 frontend tests, lint/build passed. Browser: normal empty-state, isolated real-model suggested-question answer ($80/$90/$100 for 16802 Oct 10), keyboard submit, 390 px no-overflow checks passed. Evidence is linked in `docs/rag-context.md` and report.
- Normal app remains running on 8000/5173 for user testing. Isolated 8001/5174 services stopped after checks. User must search a ZIP and Add to Local before comparisons; builtin examples then fill exact ZIP/date inputs.


## App running for student testing

- Started normal backend on `127.0.0.1:8000` and frontend on `127.0.0.1:5173` at the user’s request. Uses the normal database and real OpenAI configuration, not mock data.
- Services intentionally left running for testing. Backend exec session `31182`; frontend session `62827`.


## Live OpenAI verification — October 8, 2026

- User privately configured `OPENAI_API_KEY`; detected and verified against real OpenAI requests with app model `gpt-4.1-mini`. User confirmed **GPT-6 Astra** as the development assistant model; disclosure updated.
- Real multi-night answer: Hotel State College $180; Scholar Hotel $200 for October 11–13. Follow-up Oct 12: $90/$120. No-match Oct 20: empty data correctly explained. Test data uses first four places from previously captured Geoapify JSON, with explicitly simulated rates in an isolated DB; normal saved-hotel collection was empty and unchanged.
- Live tests exposed and fixed: conflicting stage instructions, missing single-night checkout, and an active rejected-query cursor retaining a read lock during error persistence. Accept verified nightly-rate projection for single-night queries only. New targeted regression coverage added.
- 218 backend tests pass (36 RAG); frontend source unchanged since 44 tests/lint/build passed. Real answers loaded in frontend after backend restart. Full live trace and screenshot are in `docs/evidence/assignment2-rag/live-verified-trace.json` and `docs/screenshots/assignment2-rag-live-answer.jpg`. Failed attempts are retained and disclosed.
- Local live-test database: `/var/folders/2j/869l7_ps6gn5thqlvp6xswwc0000gn/T/expedia-rag-live-d8w00_a2/live.sqlite3`. Test services on 8001/5174 stopped after verification.
- Remaining: student recording URL, reviewed publication/assessed commit and instructor-accessible artifact links. No longer blocked on provider/key/model disclosure.



## Part 2.2 RAG implementation checkpoint — October 8, 2026

- Branch `rag_integration`, created from `assignment2_part2_in_class` with all existing uncommitted work preserved. New work also remains uncommitted.
- Added OpenAI two-stage SQL/answer controller, backend-only key/model configuration, startup-loaded `prompts/hotel-assistant.md`, bounded read-only SQLite queries and independent full-stay/ZIP/total validation. No dependencies installed.
- Additive schema v5 adds shared local conversations and stage-labeled message traces. Existing IDs, bookings, saved hotels and manually edited demo rates are preserved; no normal database mutations were used for verification.
- Vue chatbot below discovery supports pending/error/empty/answer states, follow-up history, new/load conversation, keyboard operation and inspectable SQL/record/request trace.
- Final checks: 215 backend tests (33 RAG), 44 frontend tests, both frontend linters and build passed. Existing Starlette warning remains. Browser mock checks passed two-night totals, no matches, blocked DELETE, simulated 429, keyboard list/map/send, refresh and restart of both services. All 25 trace rows matched after restart; 4 fixture hotels/19 nights intact. 390 px mobile width had no overflow.
- Mock evidence is explicitly labeled; full trace, fixed JSON and screenshots are in `docs/evidence/assignment2-rag/` and `docs/screenshots/`. Prior Part 1 report archived to `docs/assignment2-part1-report.md`. `report.md` is now a Part 2 draft with honest pending items.
- User input needed: provider choice/private key (none configured at check), real-model verification, narrated recording URL, exact development model identity, reviewed publication/assessed commit. OpenAI `gpt-4.1-mini` is implemented provisionally; instructor `OPEN_AI` key alias supported. Do not count mock calls as live evidence.
- See `docs/rag-context.md` for reproduction, SQL, record comparisons and recording checklist. Test services created on 8001/5174 are stopped at the end of verification. Normal 8000/5173 were not running at inspection.


## Database lock correction

- The reported Remove failure was reproduced as `SQLITE_BUSY`: DB Browser held
  a pending write transaction while the user edited a demo rate and room count.
  Saved those existing edits using Write Changes to release the lock; no hotel
  was removed from the normal database during diagnosis.
- Busy/locked SQLite errors now explain how to save or revert pending DB Browser
  edits instead of using the generic unavailable message. Added temporary-database
  tests for a pending writer and a reader blocking commit, including rollback and
  successful retry. SQLite rollback journals are now explicitly Git-ignored.
- Verified the normal write lock is available and both hotel records/ten nightly
  rows remain. 24 local workflow tests and the full 182-test backend suite pass;
  both normal service health checks pass after reload. Existing Starlette warning
  remains. User can retry Remove without losing their pending demo edits.

## Assignment 2 Part 2 local workflow ready for manual verification

- Active branch: `assignment2_part2_in_class`. Added transactional local save,
  read/status and remove endpoints without changing the Part 1 discovery endpoint.
- Schema v4 adds `saved_search_locations` and `saved_hotel_zips` so searched ZIP
  context remains separate from hotel addresses. Saves create October 10–14, 2026
  demo nights with 10000-cent/20-room defaults; repeated saves preserve edits.
- Frontend checks local storage first, falls back only on successful empty lookup,
  labels source/simulated data, and keeps Add/Remove status database-backed.
  Local removal also updates map membership without changing card keyboard controls.
- Verification: 180 backend tests, 39 frontend tests, frontend lint/build passed.
  Browser mutations used `/tmp/expedia-part2-workflow-browser.sqlite3` and the
  mocked provider on 8001/5174. Save, refresh, service restart, dated values,
  delete rollback/recovery, local failure without fallback, and keyboard selection
  passed. Normal database records were unchanged by tests; original eight tables,
  rows and indexes matched the private pre-change backup exactly.
- Normal project services restarted on 8000/5173 after checking process commands
  and working directories. No dependency changes; existing Starlette warning remains.
- Stop for the user's browser/database inspection. See
  [workflow checkpoint](../docs/assignment2-part2-local-workflow.md). Changes remain
  uncommitted; earlier inspection evidence is retained.

## Assignment 2 Part 2 schema ready for inspection

- October 1: user completed manual comparison and authorized only the additive
  schema migration. Added `saved_hotels` and `demo_hotel_nights` in schema v3;
  exact provider IDs, nullable name/address, validated coordinates/dates,
  nonnegative integer demo defaults (10000 cents/20 rooms), composite nightly
  key and foreign key. Both new tables remain empty.
- Applied to `backend/data/expedia.sqlite3`; all original table definitions,
  indexes and rows matched the private pre-migration backup exactly. Repeated
  initialization preserves data; foreign-key check has no violations.
- 158 backend tests, 32 frontend tests, both frontend linters and build passed.
  Existing Starlette warning remains. Cached Part 1 browser results passed list
  Enter/map Space selection checks without additional discovery requests.
- No frontend/API/discovery/dependency changes or save workflows. Stop for user
  verification. See [schema checkpoint](../docs/assignment2-part2-schema.md).

## Assignment 2 Part 2 inspection

- October 1: active branch `assignment2_part2_in_class`; schema preparation only.
  Findings: [database and API inspection](../docs/assignment2-part2-inspection.md).
- Opened the existing `backend/data/expedia.sqlite3` in DB Browser, inspected all
  six table definitions and eight fictional hotel rows. Provider-ID mapping,
  full address, coordinates and hotel/date rate-and-room inventory are missing.
- ZIP 16802 returned 20 hotels. Captured a separate HTTP 200 response from the
  same discovery endpoint; it contains place ID, name, address and coordinates,
  but no rates or availability. Two live submissions total for this inspection.
- Network-panel inspection remains unverified because native browser developer
  tools were inaccessible. Report distinguishes the direct response capture from
  the original browser transaction and gives the remaining manual checkpoint.
- Saved schema/row JSON, response JSON and DB Browser/search screenshots under
  `docs/evidence/assignment2-part2/`. No schema, application, dependency or data
  changes; credentials and session values were not captured.

## Current application

- Hotel Finder: Vue ZIP search with FastAPI/Geoapify and synchronized Leaflet map.
  Exact five-digit U.S. ZIP, 5 km returned-point radius, 20-record cap, honest
  missing fields, distinct outcomes, keyboard controls and provider attribution.
- Header uses a teal hotel icon; hero reads “Find somewhere to stay.” The generic
  hotel illustration has no lettering. Footer: Assignment 2.1 · IST 402.
- Original fictional accounts, pricing, booking CRUD and ZIP-coordinate tools
  are available at `/?demo=booking`. No shortlist storage or normal data mutations.
- Normal services remain on 8000/5173. Leaflet 1.9.4 was explicitly approved and
  installed; no other dependency additions or upgrades were made by this work.

## Verification

- September 29: 117 backend tests, 32 frontend tests, both linters and build passed.
  One existing Starlette TestClient deprecation warning remains.
- Live 16802 returned State College and 20 places/markers with cap notice; both
  directions of list/map keyboard selection passed. Six live discovery calls
  across development/review. Fixture checks cover leading zero, missing fields,
  literal text, empty, unresolved, failure and rate limit without provider calls.
- Desktop/mobile, invalid input and separate booking view verified. Test databases
  are temporary; no normal bookings/accounts were changed. `.env` ignored/untracked;
  configured key absent from frontend build. Temporary fixture servers were stopped.

## Documentation cleanup

- User requested app-focused documentation with no repeated Canvas instructions.
  README/report/research/verification/AI evidence now describe the app directly.
  Previous report remains in docs/assignment1-report.md as historical evidence.
- Active discovery images: early mockup, final homepage, live results and mobile.
  Seven intermediate images and the now-unneeded recording/submission guides moved
  to /tmp/hotel-finder-documentation-archive-2026-09-29 for local recovery, outside
  the repository. Earlier booking and ZIP screenshots remain linked by older records.
- Report names GPT-6 Astra, confirmed by the user. User will attach the supplied
  video separately with the report; no hosted URL is requested or pending.
  Companion video filename: IST 402 - Assignment 2.1 SR.mov.
- Reviewed implementation and evidence published in commit `3e432bcb22d0cd24ae8e78538de1958deb6e8237`.
  Report links are pinned to this assessed revision. The report is finalized in
  a subsequent documentation commit so its text can include the implementation SHA.
- User explicitly approved publication to tmy5235/Expedia-Clone on main after the
  initial automatic approval rejection. Implementation commit 3e432bc and finalized
  report commit 294eecd were pushed successfully.
- Verified 13 public repository/report/evidence URLs without authentication, with
  TLS verification enabled. Published report matches the local file byte for byte.
  No course submission occurred; user will upload report.md and the companion video.

## Documentation validation

- Checked 64 local Markdown links; every target exists. Current documents have
  balanced code fences and whitespace checks pass. Refreshed retained homepage
  screenshots to reflect the final footer; app source was not changed in cleanup.
