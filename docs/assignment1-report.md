# Expedia Clone — Part 2: MVC, Accounts, and Personalized Pricing

## Repository and revision

Repository: <https://github.com/tmy5235/Expedia-Clone>

Implementation checkpoint:
[`5b4e1161620ea2dec398293152d9e0148be3a82f`](https://github.com/tmy5235/Expedia-Clone/commit/5b4e1161620ea2dec398293152d9e0148be3a82f).

Submission branch: [`main`](https://github.com/tmy5235/Expedia-Clone/tree/main).
Development branch: `codex/part-2-accounts-pricing`.
This report and the final handoff are recorded in a documentation commit after
the implementation checkpoint. [View the submission report on GitHub](https://github.com/tmy5235/Expedia-Clone/blob/main/report.md).

This revision extends the previous Part 2 merge,
`4daf427a8fd9d5c632d6144b4f34b03120784cd0`. The preserved Part 1 checkpoint is
`627cda2c36dfab77ffbf7cc74ff363a4198b8c17`.

## Implementation and MVC responsibilities

The existing FastAPI/Vue application retains hotel search and booking creation,
history, cancellation, and deletion. This revision replaces traveler selection
with account creation, login, and logout and adds the optional Activity 3 pricing
exercise. All records and credentials are fictional and local.

| MVC role | Account feature | Personalized pricing feature |
| --- | --- | --- |
| Model | SQLite users retain IDs/display names and gain unique usernames and demo passwords. Sessions reference users. The migration preserves booking relationships and existing changes. | One shared history table stores user ID, normalized query, UTC timestamp, local calendar date, and count at submission. Hotels retain base rates; bookings save accepted totals. |
| View | `AccountPanel.vue` provides account/login/logout controls, signed-in username, and feedback. `BookingHistory.vue` shows the current user's saved bookings. | `App.vue` renders the nightly price and total returned by the backend. `useSearch.js` handles requests and stale results; no pricing rule runs in Vue. |
| Controllers | `controllers/accounts.py` creates accounts, checks credentials, and resolves the current user. FastAPI handlers validate requests and enforce booking ownership. | `controllers/search.py` coordinates the database, `urgency.py` determines the calendar day and threshold, and `pricing.py` applies the increase. `database.py` handles parameterized persistence and history counting. |

The [design note](https://github.com/tmy5235/Expedia-Clone/blob/5b4e1161620ea2dec398293152d9e0148be3a82f/docs/design.md) maps the changed files and data in more detail.
The original CSV-reading implementation remains in `hotel_search.py`; current
application reads use SQLite after the one-time seed.

## Rules and account behavior

Usernames are case-insensitive, unique, and restricted to 3–40 letters, digits,
or underscores. Passwords are case-sensitive and readable in SQLite, as permitted
for this classroom activity. Existing users log in as `traveler1`–`traveler6`
with the made-up password `classroom-demo`; their original IDs do not change.
New accounts receive unique UUID-based IDs. No real personal credentials are used.

The backend tracks login with an opaque session cookie and a SQLite session row.
Logout deletes the session and clears displayed user data. A caller cannot manage
another user's bookings by supplying a different `user_id`.

Every submitted nonempty search by a signed-in user is recorded, including a
search with no matches. Matching ignores capitalization and surrounding spaces.
The count includes the current submission and is scoped to user, normalized query,
and calendar day in **America/New_York**, including daylight saving changes.
Searches 1–3 return the stored base rate. Search 4 onward returns **base × 1.20**,
rounded to cents, with no compounding. Anonymous searches use the base rate and
create no history. A different query or the next local day starts a separate count.
Repeated searching is an assumed urgency signal for this exercise; it does not
prove that the traveler is in a hurry.

A booking request includes the selected search ID. The backend checks search ownership
and the chosen trip, calculates its rate from the saved submission count, and
saves the total. Later searches do not change existing booking totals.

## Verification evidence

Verification ran on September 21, 2026 in America/New_York using an isolated
SQLite database and ports 8001/5174. Existing services on 8000/5173 were left running.
No application dependencies were installed or upgraded. With permission, DB
Browser for SQLite 3.13.1 was installed from the official Homebrew cask and opened
against the verification database.

| Check | Observed evidence |
| --- | --- |
| Backend regression tests | 28 passed, using temporary databases. Includes one-time seeding, version-1 migration, rollback, IDs/foreign keys, authentication, ownership, pricing, concurrent counts, rounding, and restart persistence. One existing TestClient deprecation warning remains. |
| Frontend tests and checks | 14 tests passed; Oxlint, ESLint, and production build passed. |
| Final documentation checkpoint | All 15 project-owned Markdown files audited; outdated account/search descriptions corrected, historical prompts labeled, local links checked, and report screenshots and setup/design/verification links pinned to the implementation commit. Automated tests, lint/build, and whitespace checks passed again before publication. |
| Create account and reject duplicates | `class_user_a` created successfully. Reusing its username showed “That username is already taken.” |
| Incorrect login | Wrong password showed “Incorrect username or password.” with no signed-in user. Backend tests also cover an unknown username. |
| User A matching searches | Valley Trail Inn, H008/T008: searches 1, 2, 3 showed $100/night and $200 total; searches 4 and 5 showed $120/night and $240 total. Capitalization/space variants used the same count. |
| Different query | A's first `Valley` search showed count 1 and $100/night, despite prior `Valley Trail` searches. |
| Different user | `class_user_b` saw count 1 and $100/night for `Valley Trail`, with empty booking history. |
| Next day | Injected-clock backend tests verified count resets at New York midnight, including daylight saving boundaries. The machine clock was not changed. |
| Booking CRUD | A created a $240 T008 booking, read it after refresh, cancelled it with the row and price retained, then created and deleted a separate $200 test booking. |
| Logout | Signed-in username, booking history, and previous search results disappeared. The backend rejects booking requests without a valid session. |
| Both-service restart | B's session survived. A could log back in; its cancelled $240 booking remained and the deleted booking stayed absent. A's next matching search continued at count 6 and $120/night. |
| Stored model | H008 remained `nightly_rate_cents = 10000`; `PRAGMA foreign_key_check` returned no rows. Original user/booking references remain valid; no records were reseeded. |

![Signed-in user A, sixth matching search at $120, and saved cancelled $240 booking after restart](https://github.com/tmy5235/Expedia-Clone/blob/5b4e1161620ea2dec398293152d9e0148be3a82f/docs/screenshots/part2-accounts-pricing.png?raw=true)

A final seventh-search screenshot also confirms the rate remains $120:

![User A still sees $120 on search seven](https://github.com/tmy5235/Expedia-Clone/blob/5b4e1161620ea2dec398293152d9e0148be3a82f/docs/screenshots/part2-personalized-price.png?raw=true)

The four older Part 2 screenshots in `docs/screenshots/` show the earlier
traveler-selection interface and remain historical evidence only.

## Trace: View → Controllers → Model → View

1. In the Vue hotel-name form, `class_user_a` submitted `VALLEY TRAIL` for the
   fourth time. `useSearch.submitSearch()` called the stay API.
2. The FastAPI handler read the session cookie. The account controller resolved
   A's stored `user_id`: `U-111d1c78533c46e5bea768776cd88167` in this isolated run.
3. The search controller normalized the query to `valley trail` and retrieved
   H008/T008. The database controller inserted search-history row 4 with A's user
   reference, a UTC timestamp, local date `2026-09-21`, and `search_count = 4`.
   The count and insertion occurred inside one write transaction.
4. The urgency controller identified the fourth same-user/query/day submission.
   The pricing controller used the unchanged 10000-cent base rate to return
   12000 cents per night and 24000 cents for two nights.
5. Vue displayed **$120.00** and **$240.00** directly from those returned fields.
   Search 5 still returned $120, confirming that the increase did not compound.
6. Booking from search 5 saved booking
   `B-745cdaf519ba44ea8cf75b5a5c4550d6` at 24000 cents. Its cancelled row remained
   after refresh and restart, while H008's base rate remained 10000 cents.

The changed Model records are the new account/session/history records and the
saved booking total. The changed Controllers calculate per-user daily pricing.
The changed View collects credentials, shows identity/feedback, and renders
backend prices. The stored history and unchanged hotel rate explain the observed
result without relying on frontend-only state.

## Project resources and limitations

The repository's `main` branch contains the implementation and final report;
the implementation commit linked above identifies the tested code and evidence.
Setup and demo credentials are documented in the
[README](https://github.com/tmy5235/Expedia-Clone/blob/5b4e1161620ea2dec398293152d9e0148be3a82f/README.md).
The [verification guide](https://github.com/tmy5235/Expedia-Clone/blob/5b4e1161620ea2dec398293152d9e0148be3a82f/docs/verification.md)
contains repeatable checks and DB Browser queries.

Limitations: fictional local classroom app; readable demo passwords and simple
sessions; no production authentication, payments, room inventory, or live
reservation service. The supplied activity text guided implementation because
the linked Canvas lecture was not accessible from the research tool.
