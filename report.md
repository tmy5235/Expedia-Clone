# Expedia Clone — Part 1

## Repository and commit

Repository URL: <https://github.com/tmy5235/Expedia-Clone>

Exact Part 1 implementation commit: [`627cda2c36dfab77ffbf7cc74ff363a4198b8c17`](https://github.com/tmy5235/Expedia-Clone/commit/627cda2c36dfab77ffbf7cc74ff363a4198b8c17)

## Implementation

The Vue frontend provides a labeled hotel-name input, Search button, plain results table, and clear loading, error, and no-results messages. It sends search requests through the Vite `/api` proxy.

FastAPI validates the request and returns JSON from `GET /api/stays`. The Python backend reads `hotels.csv` and `trips.csv`, matches hotel names without case sensitivity, joins the records using `hotel_id`, and calculates the number of nights and total stay price.

## Verification

| Action | Expected result | Observed result |
| --- | --- | --- |
| Search for `Hotel` in the browser | Display matching stays from the supplied CSV files | Passed: displayed 8 matching stays with dates, nightly rates, and calculated totals |
| Search for `Fire` in the browser | Display a clear no-results message | Passed: displayed `No hotels matched “Fire”.` |
| Run backend tests | All hotel-search and API tests pass | Passed: 9 tests; one third-party FastAPI TestClient deprecation warning |
| Run frontend tests, Oxlint, ESLint, and production build | All checks pass | Passed: 4 tests, both linters, and the Vite build |
| Manually review changed files in VS Code | Student confirms the implementation is understood and accepted | Passed: student confirmed the files looked good on September 11, 2026 |

Successful search:

![Hotel search showing matching stays in the results table](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/screenshots/part1-search-results.png?raw=true)

No-results search:

![Fire search showing the no-results message](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/screenshots/part1-no-results.png?raw=true)

## Project context and next steps

Project context: [README](https://github.com/tmy5235/Expedia-Clone/blob/main/README.md), [AGENTS](https://github.com/tmy5235/Expedia-Clone/blob/main/AGENTS.md), [design note](https://github.com/tmy5235/Expedia-Clone/blob/main/docs/design.md), [selected prompts](https://github.com/tmy5235/Expedia-Clone/blob/main/prompts/README.md), and [current handoff](https://github.com/tmy5235/Expedia-Clone/blob/main/handoffs/current.md).

Remaining limitation: SQLite booking CRUD is reserved for Part 2. The next task is to implement Part 2 on a feature branch.
