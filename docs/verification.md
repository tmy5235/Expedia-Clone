# Verification

## Live discovery

The current feature's expected/observed record, fixture-server instructions,
and limitations are in [Discovery verification](assignment2-verification.md).
September 29 checks: 117 backend tests, 32 frontend tests, lint/build passed;
live ZIP 16802 and simulated browser error/keyboard/mobile states verified.

## ZIP input and table

1. Open `/api/health` on the backend and record only its configuration status.
2. Check `/api/demo/zip-location` directly for the fixed `16802` milestone.
3. In the Vue ZIP panel, submit `16802` and confirm the table matches the response.
4. Enter a different ZIP and confirm the new value is used. Editing the input
   must clear the old table. Invalid input such as `123` must show validation.
5. Verify the hotel-name search still returns matching stays.
6. Capture the entered ZIP and returned table; exclude keys and `.env` contents.
   The health status may be stated separately in the submission note.

Each successful live lookup consumes provider quota; routine checks use the
mocked backend and frontend tests. The September 24 extension verification
passed 97 backend tests, 23 frontend tests, both frontend linters, and the
production build. A pre-existing third-party TestClient deprecation warning
remains. See [ZIP verification evidence](zip-lookup-submission.md).

## Automated checks

Run with the existing dependencies; no upgrades are required:

```bash
cd backend
.venv/bin/python -m pytest -q
```

```bash
cd frontend
npm test
npm run lint
npm run build
```

Tests use temporary databases. Backend coverage includes migration from version 1,
one-time seed, rollback, foreign keys, accounts, duplicate/invalid credentials,
sessions, logout, protected booking CRUD, independent user/query counts,
normalization, empty results, anonymous/blank searches, concurrent submissions,
cent rounding, and New York midnight boundaries including DST. Injected clocks
verify next-day behavior without changing the machine clock.

## Isolated browser run

Check ports before starting services; never stop unrelated processes. Defaults
are backend 8000/frontend 5173. The README provides 8001/5174 commands with a
temporary database and `EXPEDIA_API_TARGET` if defaults are occupied.

1. Create fictional accounts A and B with a made-up password. Try A again and
   confirm duplicate feedback. Incorrect username/password must leave you logged out.
2. Log in as A. Search `Valley Trail` five times, varying capitalization and
   surrounding spaces. Counts 1, 2, 3 return $100/night ($200 for T008); 4 and 5
   return $120/night ($240). No compounding.
3. Book T008 at $240; refresh and confirm the signed-in username and saved total.
   Cancel it and confirm the row remains cancelled at $240.
4. Search `Valley`; this different query starts at one with $100/night. Create
   a second disposable booking and delete it with the in-page confirmation.
5. Log out. Username, history, and old search results must disappear. Log in
   as B; its first `Valley Trail` search remains $100 and its history is empty.
6. Restart both services with the same temporary database. Refresh: B's session
   survives. Log out/in as A: cancelled booking remains; deleted booking is absent.
   Submit `Valley Trail` again: count continues at six, $120/night.
7. Search a nonexistent hotel and verify the no-results message. Blank input
   shows validation and creates no history.
8. Log in as `traveler1` / `classroom-demo` and confirm preserved seeded bookings.
9. Inspect the database using DB Browser for SQLite. Confirm base rate and IDs
   remain unchanged, no seed duplicates, and valid foreign keys.
10. Stop only the services created for this verification unless asked to keep them running.

## Read-only database evidence

Open the same database in DB Browser for SQLite. Browse `users` and
`search_history` or use **Execute SQL**:

```sql
SELECT u.user_id, u.username, s.search_id, s.query, s.searched_at,
       s.search_day, s.search_count
FROM search_history s JOIN users u USING (user_id)
ORDER BY s.search_id;

SELECT hotel_id, hotel_name, nightly_rate_cents
FROM hotels WHERE hotel_id = 'H008';

SELECT booking_id, user_id, trip_id, status, total_cents FROM bookings;
PRAGMA foreign_key_check;
PRAGMA user_version;
```

Expected H008 rate: `10000` cents. Foreign-key check: no rows. Schema version: 2.
New account IDs start `U-`; original `U001`–`U006` and their booking references remain.
A fresh verification run ends with 8 hotels, 12 trips, 8 users (6 supplied + A/B),
and 7 bookings (6 supplied + the cancelled test booking).

## Latest evidence (September 21, 2026, America/New_York)

- Backend: 28 tests passed; one existing third-party TestClient deprecation warning.
- Frontend: 14 tests, Oxlint, ESLint, and production build passed.
- Browser: registration, duplicate rejection, incorrect password, login/logout,
  $100/$120 threshold, query normalization, independent query/user pricing,
  create/read/cancel/delete, refresh, and both-service restart all passed.
- Automated clocks verified next-day resets and DST boundaries.
- Database: original $100 base rate, valid foreign keys, retained cancelled $240
  booking, and deleted booking absent after restart.
- [Screenshot: personalized pricing and cancelled booking after restart](screenshots/part2-accounts-pricing.png).
- The earlier screenshots document the original traveler-selection UI and are
  retained as historical Part 2 evidence, not the current account interface.


## Submission documentation checkpoint

Audit all project-owned Markdown files, including AGENTS, both application
READMEs, the supplied-data guide, design/verification, historical prompt notes,
the handoff, and report. Exclude dependency, environment, cache, build, and Git
internal files. Keep historical facts labeled and make current accounts, MVC,
pricing, and persistence descriptions consistent. Validate local links and
screenshots; use permanent GitHub links in the standalone submission report.
Run the automated checks above and `git diff --check` before publication.
