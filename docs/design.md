# Expedia Clone Design

Expedia Clone keeps a clear boundary between the Vue interface, FastAPI routes,
and SQLite-backed Python services.

## Responsibilities

| Area | Responsibility |
| --- | --- |
| Vue frontend | Collect hotel-name searches and traveler choices; display stays and saved booking history; send create, cancel, and delete requests; show loading, empty, success, confirmation, and error states. |
| FastAPI | Validate query, path, and request-body IDs; expose stay, traveler, and booking routes; return saved results and clear status codes. |
| Python backend | Seed the four supplied CSV files once, enable foreign keys, query joined SQLite records, calculate stay totals, and commit booking changes. |

## Data flow

The first database startup creates hotel, trip, user, and booking tables in one
transaction and imports the fictional starter records. A schema version marker
prevents later starts from importing them again. After that seed, every
application read and write uses SQLite.

Vue sends a hotel query to FastAPI, which joins hotels and trips in SQLite. A
booking request connects the selected traveler to a trip and receives a
new unique ID. History joins all four tables. Cancellation updates the status
to `cancelled`; deletion removes only the identified booking owned by the
selected traveler. The interface uses standard booking terminology; all
supplied records remain fictional classroom data.
