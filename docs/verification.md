# Verification

Run all commands from the `expedia-clone` project unless a step changes directories.

## Automated checks

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

## Development services

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`
- Vite forwards frontend `/api` requests to the backend.

Before starting either service, confirm its port is available. Never stop a process that was not started for the current verification run.

## Application checks

- Search for a hotel from the supplied CSV data and confirm its available stays appear.
- Search for a hotel that does not exist and confirm a clear no-results message appears.
- Select Traveler 6, confirm its seeded history is empty, then create and read a booking through the frontend.
- Cancel a booking and confirm the record remains with a cancelled status.
- Create a second test booking, delete it after the in-page confirmation, and confirm it is removed.
- Refresh and restart both services with the same database, then confirm saved changes remain and starter records are not duplicated.

For an isolated manual run, set `EXPEDIA_DB_PATH` to a path under `/tmp` before
starting FastAPI. Do not use the normal application database for destructive
verification.

## Part 2 evidence

- [Hotel search and empty history](screenshots/part2-search-results.png)
- [Two created bookings in history](screenshots/part2-booking-confirmation.png)
- [Cancelled booking retained in history](screenshots/part2-booking-cancellation.png)
- [Deleted booking removed from history](screenshots/part2-delete-booking.png)
