# Expedia Clone — Part 2

## Repository and commit

Repository URL: <https://github.com/tmy5235/Expedia-Clone>

Exact Part 2 commit:
[`e392a6667b354d56cb69f30d1145e111702d7dd9`](https://github.com/tmy5235/Expedia-Clone/commit/e392a6667b354d56cb69f30d1145e111702d7dd9)

Reviewed merge commit:
[`4daf427a8fd9d5c632d6144b4f34b03120784cd0`](https://github.com/tmy5235/Expedia-Clone/commit/4daf427a8fd9d5c632d6144b4f34b03120784cd0)

Preserved Part 1 checkpoint:
[`627cda2c36dfab77ffbf7cc74ff363a4198b8c17`](https://github.com/tmy5235/Expedia-Clone/commit/627cda2c36dfab77ffbf7cc74ff363a4198b8c17)

## Implementation

Since Part 1, the Python backend has added a persistent SQLite database. On its
first startup, it creates hotel, trip, user, and booking tables and imports the
four supplied CSV files. Later starts reuse the saved database without
duplicating or restoring starter records. Search now reads SQLite while keeping
the same partial, case-insensitive hotel-name behavior.

The Vue frontend selects a traveler, creates bookings from search results,
reads booking history from FastAPI, cancels a booking while retaining its
history record, and deletes a test booking after confirmation.
FastAPI validates the supplied IDs and reports success only after SQLite commits
the requested change.

## Verification

| Action | Expected result | Observed result |
| --- | --- | --- |
| Check the project Python interpreter for SQLite | Built-in SQLite works without a dependency installation | Passed: Python environment reported SQLite 3.50.4; a row survived closing and reopening a temporary database |
| Run backend tests | Search, one-time seed, ID validation, foreign keys, CRUD, rollback, and restart persistence pass using temporary databases | Passed: 17 tests; one third-party FastAPI TestClient deprecation warning |
| Run frontend tests, Oxlint, ESLint, and production build | API and booking-state tests and all frontend checks pass | Passed: 9 tests, both linters, and the Vite production build |
| Select Traveler 6 in the browser | Show a clear empty-history state | Passed: displayed `No bookings for this traveler yet.` |
| Search for `Harbor Lantern` and book T001 and T009 | Create unique bookings beyond the seeded examples and read both from saved history | Passed: both confirmed bookings appeared with different booking IDs, stay details, dates, prices, and booking dates |
| Refresh the browser | The created bookings remain in history | Passed: both records remained after the history was loaded again |
| Cancel the new T009 booking | Retain the row and change its status to cancelled | Passed: the same T009 booking ID remained with `cancelled` status while T001 stayed confirmed |
| Delete the new T001 test booking | Remove only the selected test booking | Passed: T001 disappeared after the in-page delete confirmation while cancelled T009 remained |
| Restart the frontend and backend with the same verification database | Created and cancelled data remains, deleted data stays absent, and seed rows are not duplicated | Passed: 8 hotels, 12 trips, 6 users, and 7 bookings remained; the seventh booking was the retained cancelled T001 test record |
| Search for `Fire` after restart | Preserve the Part 1 no-results behavior | Passed: displayed `No hotels matched “Fire”.` |
| Review the customer-facing language in the browser | The interface reads like a normal booking website | Passed: student approved `Traveler`, `Booking`, and `Booking history` on September 15, 2026 |
| Manually scan the complete changed files | Student understands and accepts the submitted feature-branch changes and documentation | Passed: student approved the complete implementation, documentation, report, and screenshots on September 15, 2026 |

Hotel search and initial empty history:

![Part 2 hotel search showing Traveler 6, two Harbor Lantern stays, booking actions, and empty booking history](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/screenshots/part2-search-results.png?raw=true)

Created bookings:

![Part 2 booking history showing two newly created confirmed bookings with unique IDs](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/screenshots/part2-booking-confirmation.png?raw=true)

Cancelled booking retained in history:

![Part 2 booking history showing T009 retained with cancelled status while T001 remains confirmed](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/screenshots/part2-booking-cancellation.png?raw=true)

Deleted booking removed:

![Part 2 booking history showing T001 removed while the cancelled T009 record remains](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/screenshots/part2-delete-booking.png?raw=true)

## Project context and next steps

Project context: [README](https://github.com/tmy5235/Expedia-Clone/blob/main/README.md),
[AGENTS](https://github.com/tmy5235/Expedia-Clone/blob/main/AGENTS.md),
[design note](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/design.md),
[selected prompts](https://github.com/tmy5235/Expedia-Clone/blob/main/prompts/README.md),
and [current handoff](https://github.com/tmy5235/Expedia-Clone/blob/main/handoffs/current.md).

Remaining limitations: the application uses only fictional classroom records;
it has no authentication, payments, room inventory, or connection to a live
reservation service. The next task is to upload this `report.md` file to the
Part 2 submission page and submit the assignment.
