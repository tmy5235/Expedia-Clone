# Expedia Clone Frontend

This Vue 3 interface uses the Composition API with `<script setup>` and Vite.
It provides the complete Part 2 hotel search and booking workflow while FastAPI
and SQLite own all persistent data.

## Responsibilities

- Search for full or partial hotel names and display matching stays in a labeled table.
- Select a traveler and read that traveler's booking history from FastAPI.
- Create a booking from a search result, cancel it while retaining the history row, and delete a test booking after confirmation.
- Present clear loading, empty, success, validation, and request-error states.
- Keep only temporary interface state in Vue; never treat frontend state as persistent storage.
- Remain readable on phone and desktop with keyboard focus and accessible table headings.

The interface uses standard traveler and booking terminology. The underlying
records are the fictional course data described in
[`expedia-clone-data/README.md`](../expedia-clone-data/README.md).

## Commands

From `frontend/` with the existing dependencies:

```bash
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
npm test
npm run lint
npm run build
```

Vite proxies `/api` to `http://127.0.0.1:8000`, so both services must be
running for browser checks. See the [root setup](../README.md),
[design note](../docs/design.md), and [verification guide](../docs/verification.md).
