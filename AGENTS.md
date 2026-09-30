# Project Rules

## Scope

- Keep backend code in `backend/` and frontend code in `frontend/`.
- Prefer small, focused changes that preserve the separation between the API and UI.
- Use the fictional records in `expedia-clone-data/`; do not add real traveler, payment, or reservation data.
- Do not commit secrets, local environment files, virtual environments, dependency directories, build output, caches, or SQLite database files.

## Backend

- Use FastAPI and Python type annotations.
- Place application code under `backend/app/`.
- Keep route handlers concise; move CSV access, database access, and reusable business logic into dedicated modules.
- Read the supplied CSV files with Python for the initial search feature and connect hotels to trips using `hotel_id`.
- Use Python's `sqlite3` module for persistent hotel, trip, user, and booking data.
- Preserve supplied IDs and assign unique IDs to new bookings.
- Seed SQLite only when the database is first created. Starting the app again must not duplicate starter records or overwrite created, cancelled, or deleted bookings.
- Validate IDs and booking changes on the server. Return success only after a database change is saved.
- Use parameterized SQL and enable foreign-key checks.
- Add or update tests whenever backend behavior changes. Tests must use temporary databases and must not modify normal application data.

## MVC, Accounts, and Personalized Pricing

- Keep SQLite persistence and migrations in the Model; keep account, search, urgency, and pricing logic in backend controllers; keep Vue focused on input and presentation.
- Preserve original user IDs, booking references, and saved changes when migrating the database. Never reseed an existing database.
- Account usernames are unique and case-insensitive. Use only fictional credentials; readable passwords are permitted for this classroom exercise.
- Resolve the current user from the server-managed session. Require that user to own every booking read or mutation; logout invalidates the session.
- Record each signed-in, nonempty search, including no-match searches. Normalize queries by trimming and casefolding. Count the current submission atomically with prior matching searches for that user and calendar day in `America/New_York`.
- Searches 1–3 return base price; search 4 onward returns base × 1.20 once. Keep hotel base rates unchanged and preserve the accepted total on saved bookings.
- Vue displays backend prices and clears stale results/history when the current account changes. Anonymous searches are unrecorded and use base prices.
- Verify account errors, per-user/query/day isolation, the $100 → $120 threshold, migration, booking CRUD, and restart persistence. See `docs/design.md` and `docs/verification.md`.

## Assignment 2 — Live Discovery

- Preserve the original fictional search, accounts, prices, bookings, and SQLite data.
  Public hotel-place information belongs to a separate discovery feature and must
  never be presented as a priced or bookable sample stay.
- Model: validated external-place schemas; existing SQLite storage/migrations remain
  in the Model. Controllers: exact U.S. ZIP resolution, Geoapify requests, radius,
  limits, normalization, and safe errors. Vue: input, list/map selection, and feedback.
- Use string ZIPs, exact country/postcode verification, and a 5 km radius about
  the returned point. Keep provider IDs and honest missing-field labels. Preserve
  attribution; do not invent rates, ratings, availability, or reservations.
- Geocoding and Places keys stay in the backend `.env`; never copy them into Vite
  configuration. Use mocked failures and rate limits rather than exhausting quota.
- Dependency loop: CHECK the environment, explain the exact installation and get
  the student's approval, TAKE ACTION, then VERIFY the installed version and checks.
- Verification loop: state expected behavior, run the smallest relevant test,
  correct in-scope failures, rerun affected checks, and record expected/observed
  evidence. Run regression tests, lint/build, and browser list/map/keyboard checks.
- Assignment 2 Part 1 has no shortlist persistence. Add shortlist storage only
  when Part 2 is authorized. Keep the early mockup and report evidence accessible.

## Frontend implementation

- Use Vue 3 with the Composition API and `<script setup>`.
- Place application source under `frontend/src/`.
- Keep components focused and extract shared behavior into composables when appropriate.
- Provide clear loading, empty, validation, and error states.
- Use standard traveler and booking language in the interface while keeping all records fictional and local.
- Read search results and booking history from the backend. Do not use local frontend state as persistent storage.
- Support booking creation, history, cancellation, and deletion through the frontend.
- Add or update tests whenever frontend behavior changes.

## Validation

- Run the relevant tests and linters before considering a change complete.
- Verify changed frontend flows in the browser.
- Check that SQLite changes remain after browser refresh and application restart.
- Do not install or upgrade dependencies unless the task explicitly requires it.
- Document new setup steps or environment variables in `README.md`.
- Keep `handoffs/current.md` accurate as work progresses.

## Course Macros

### AutoLoop

Trigger: When the user says **“AutoLoop”**, perform a bounded fix-and-verify loop.

1. Read `AGENTS.md`, `README.md`, and the relevant verification instructions.
2. State the acceptance check for the current task.
3. Run the smallest relevant check.
4. If the check fails for an in-scope source-code reason, inspect the evidence, make the smallest relevant correction, and rerun the check.
5. Repeat for no more than five correction cycles.
6. Stop early and ask for direction if the next action requires a dependency change, machine-level permission, destructive action, an unrelated process to be stopped, or broader scope.
7. Report every cycle, the final evidence, and anything not verified.

### SmokeTest

Trigger: When the user says **“Run the smoke test”**, verify the working application without changing source code or dependency declarations.

1. Read `AGENTS.md`, `README.md`, and `docs/verification.md`.
2. Run the backend tests and frontend tests, lint, and production build.
3. Check the intended backend and frontend ports. Never stop an unrelated process.
4. Start only the services needed for the test.
5. Verify hotel search through the frontend and confirm matching stays are displayed.
6. Verify create account, duplicate rejection, invalid login, login/logout, and personalized pricing through the frontend; then verify booking create, read, cancel, and delete as the signed-in owner.
7. Confirm saved changes remain after refresh and restarting both services with the same test database.
8. Unless the user asks to keep the app running, stop only the processes created by the smoke test.
9. Report the checks performed, their results, and anything not verified.

### Combined Trigger

When the user says **“AutoLoop: run the smoke test”**, run the SmokeTest macro. If an in-scope check fails, use the AutoLoop rules to make the smallest correction and repeat the smoke test until it passes, five correction cycles are exhausted, or a stopping condition is reached.
