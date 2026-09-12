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
- After booking CRUD is implemented, create and read a booking through the frontend.
- Cancel a booking and confirm the record remains with a cancelled status.
- Delete a test booking and confirm it is removed.
- Refresh and restart both services with the same database, then confirm saved changes remain and starter records are not duplicated.

Part 1 search checks are available. Booking CRUD and persistence checks remain unavailable until Part 2 is implemented.
