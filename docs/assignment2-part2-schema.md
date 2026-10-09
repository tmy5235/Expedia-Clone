# Assignment 2 Part 2 schema checkpoint

Historical schema v3 checkpoint; empty-table observations below describe that
time. Current schema v5 includes local ZIP context and RAG history; see
[RAG verification](rag-context.md).

This records the completed schema-only checkpoint. The subsequent authorized
[local workflow](assignment2-part2-local-workflow.md) adds ZIP associations in
schema version 4 and connects saving, removal and local-first search.

Implemented October 1, 2026, on `assignment2_part2_in_class`. The user completed
the manual field comparison and authorized schema changes only. The database now
has `saved_hotels` and `demo_hotel_nights`; both are empty for inspection.

Database file:
`/Users/trevoryuhaniak/Documents/ChatGPT/expedia-clone/backend/data/expedia.sqlite3`.
The instructor's `backend/db/expedia.sqlite3` is not this project's configured path.

## API field mapping

| Existing discovery response | `saved_hotels` column | Constraint |
| --- | --- | --- |
| `hotels[].place_id` | `hotel_id` | TEXT NOT NULL primary key; binary comparison preserves exact IDs and prevents duplicates |
| `hotels[].name` | `name` | Nullable TEXT |
| `hotels[].address` | `address` | Nullable TEXT |
| `hotels[].latitude` | `latitude` | Required numeric value from −90 through 90 |
| `hotels[].longitude` | `longitude` | Required numeric value from −180 through 180 |

The mapping is documented in the migration and tested with parameterized inserts.
No save endpoint, automatic import, or frontend control was added.

## Daily demo inventory

`demo_hotel_nights` contains:

- `hotel_id`: required foreign key to `saved_hotels.hotel_id`.
- `stay_date`: required valid calendar date in `YYYY-MM-DD` format, years 0001–9999.
- `nightly_rate_cents`: required nonnegative integer, default `10000` ($100.00).
- `rooms_available`: required nonnegative integer, default `20`.

The composite primary key `(hotel_id, stay_date)` allows only one row per hotel
and night. Different nights and different hotels remain independent. Foreign-key
checks are enabled on every application database connection; deleting a referenced
hotel or changing its ID cannot leave orphan nightly rows. SQLite tools opening
their own connections must also enable `PRAGMA foreign_keys = ON`.

**Rates and room counts are fictional classroom defaults.** They do not come from
Geoapify and do not establish real-world prices or availability. Defaults apply
when a nightly row is later inserted with those columns omitted. Migration does
not generate hotels, dates, or inventory.

## Migration and preservation

`Database.initialize()` runs version 2 → 3 under its existing `BEGIN IMMEDIATE`
transaction. Version 1 first receives the existing account migration; fresh
databases are seeded once and migrate through to version 3. Repeated startup at
version 3 performs no schema or seed changes. A failed migration rolls back both
DDL and version changes; unsupported schema versions are rejected.

A private local SQLite backup was taken before edits, outside the repository.
After migration, all six original tables' SQL definitions, indexes and row values
were compared with that backup and were identical, including saved booking and
account changes. Only the two new tables/indexes and schema version were added.
Credential and session values were not printed or captured in evidence.

## Verification results

| Check | Expected | Observed |
| --- | --- | --- |
| Baseline backend suite | Existing behavior passes before changes | 117 passed |
| Targeted schema, accounts and discovery tests | Migration, constraints, persistence and frozen discovery remain valid | 75 passed |
| Final backend suite | Full regression passes using temporary databases and mocked providers | 158 passed; existing Starlette deprecation warning only |
| Frontend tests | Existing behavior passes | 32 passed |
| Frontend lint and production build | No lint/build failures | Oxlint, ESLint and Vite build passed |
| Fresh, v1, v2 and repeated initialization | Reach v3 without reseeding existing data | Passed |
| Provider IDs and optional fields | Exact IDs retained, duplicates rejected, NULL names/addresses accepted | Passed |
| Coordinates, dates and numeric values | Invalid/out-of-range values rejected, leap dates and zero values accepted | Passed |
| Night uniqueness and foreign keys | Duplicate hotel/date and orphan references rejected | Passed |
| Migration failure and retry | Atomic rollback, successful retry, original data unchanged | Passed |
| Normal database preservation | Original tables and rows unchanged after repeated initialization | Exact comparison passed; v3 persisted; both new tables empty; no foreign-key violations |
| Backend reload | App reopens migrated database | Uvicorn worker restarted during reload; health check passed |
| Browser list and map keyboard behavior | Both directions keep selection synchronized | Enter on Scholar Hotel list card selected its marker; Space on Hotel State College marker selected its card |

The browser check reused already-loaded Part 1 results and made no new discovery
requests. API/ZIP regression used mocked requests. No frontend source, routes,
response models, discovery controller, dependency manifests or environment settings
were changed. No new account or booking was created in the normal database.

## Inspect in DB Browser

Reopen the database or refresh its schema view to see all eight tables. The following
queries are read-only; the foreign-key pragma enables checks for that connection:

```sql
PRAGMA foreign_keys = ON;
PRAGMA user_version;
PRAGMA table_info(saved_hotels);
PRAGMA table_info(demo_hotel_nights);
PRAGMA foreign_key_list(demo_hotel_nights);
PRAGMA foreign_key_check;
SELECT name, sql FROM sqlite_master
WHERE type = 'table' AND name IN ('saved_hotels', 'demo_hotel_nights');
SELECT COUNT(*) FROM saved_hotels;
SELECT COUNT(*) FROM demo_hotel_nights;
```

Expected: version 3, the specified columns/defaults/composite key, the foreign key
to `saved_hotels`, no foreign-key violations, and zero rows in both new tables.
Implementation stops here for the user's verification.
