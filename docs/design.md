# Expedia Clone Design

Expedia Clone uses the same frontend/backend separation as Hello Agent. This design describes the implemented Part 1 hotel search.

## Responsibilities

| Area | Responsibility |
| --- | --- |
| Vue frontend | Collect a hotel-name search and display available stays in a plain table. Show loading, empty, and error states. |
| FastAPI | Define the HTTP routes, validate requests, call backend services, and return clear JSON responses and status codes. |
| Python backend | Read `hotels.csv` and `trips.csv`, match hotel names, join records by `hotel_id`, and calculate nights and stay totals. |

## Data flow

For CSV search, Vue sends a hotel query to FastAPI. The backend reads `hotels.csv` and `trips.csv`, joins them with `hotel_id`, and returns matching stays for the results table.

Part 2 will add SQLite and simulated booking CRUD after the Part 1 checkpoint is reviewed and preserved. All supplied hotel data is fictional.
