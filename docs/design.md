# Expedia Clone — MVC Design

Part 2 uses Model–View–Controller responsibilities across Vue, FastAPI, and SQLite.
The accounts and personalized-pricing extension was planned against these existing
files and records before implementation; the table also maps the final changes.

| Role | Account changes | Search and pricing changes | Files |
| --- | --- | --- | --- |
| Model | Add unique normalized `username` and classroom `password` to existing users; retain `user_id`, `display_name`, and booking references. Store opaque login sessions. | One shared `search_history` table references users; hotel base rates remain unchanged. Bookings store the accepted total. | `backend/app/database.py`, `backend/app/migrations.py`, `backend/app/schemas.py` |
| View | Create Account, Login, Logout, signed-in username, errors and success feedback. Replace traveler selection with the current account. | Render the backend's nightly rate, total, and daily count; clear previous account results when identity changes. | `frontend/src/components/AccountPanel.vue`, `frontend/src/App.vue`, `frontend/src/components/BookingHistory.vue` |
| Controllers | Validate credentials, reject duplicates, look up users, compare passwords, save/delete sessions; enforce booking ownership. | Coordinate search/history, calculate local calendar day and urgency, then calculate the price from the stored base rate. | `backend/app/main.py`, `backend/app/controllers/accounts.py`, `search.py`, `urgency.py`, `pricing.py`; frontend API modules and `useAccount`, `useSearch`, `useBookings` composables |

## Stored model and migration

`Database.initialize()` locks the database before checking `PRAGMA user_version`.
A new database imports the supplied four CSVs exactly once, then applies the
accounts migration. Version 1 databases migrate in place to version 2 in one
transaction. Version 2 databases are reused without seeding or overwriting data.
Migration adds columns/tables; it never replaces user IDs or restores deleted
bookings. Legacy booking totals are populated from their existing trips/hotels.

- `users`: existing ID and display name plus unique username and readable demo password.
- `sessions`: random opaque token referencing a user. HTTP-only, SameSite Strict cookie;
  browser cookie lasts seven days. Logout deletes the server record and cookie.
  Classroom session records otherwise remain until logout or replacement; this is not production authentication.
- `search_history`: ID, user foreign key, normalized query, UTC ISO timestamp,
  New York calendar date, and the count at submission. An index supports counting
  by user/query/day. A write transaction serializes count plus insert.
- `hotels`: original integer-cent base rate, never changed by pricing.
- `bookings`: existing references/status plus saved total in cents.

All database connections enable foreign-key checks. SQL values use parameters;
success is returned only after commits. Passwords and session tokens are excluded
from public user responses. Booking routes verify that the requested owner is the
server's current user; guessing a user ID cannot read or change another account's bookings.

## Search and booking flow

1. The Vue form invokes `useSearch.submitSearch()` once per submission; the API
   client sends `GET /api/stays?hotel_name=...`. Page load, login, and refresh do not
   submit a search. Search responses set `Cache-Control: no-store`.
2. The HTTP controller resolves the current user from the session cookie.
   `SearchController.submit()` trims and casefolds the query and reads joined
   hotels/trips. Blank queries are rejected before inserting history.
3. For a signed-in user, the database records every valid submission, including
   no-match searches, and counts the current submission in the same transaction.
   Anonymous searches show base rates and create no history.
4. The urgency controller derives the day in `America/New_York`, including DST.
   Counts 1–3 use base price; counts 4+ use base × 1.20 once. The pricing controller
   rounds to the nearest cent (half up) and computes total = nightly rate × nights.
5. Vue displays returned cents. It contains no surge calculation. A booking sends
   the returned `search_id`; the backend verifies that it belongs to the user and
   contains that trip, calculates the quote from that submission's saved count,
   and commits the booking total. Subsequent searches cannot change saved bookings.

A different normalized query has its own count even if it matches the same hotel.
Next calendar day starts at one. Repeated searching is only an assumed urgency
signal for this exercise; it does not prove that someone is in a hurry.
