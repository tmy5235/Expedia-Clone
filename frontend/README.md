# expedia-clone frontend

Vue 3 Composition API with `<script setup>`, built with Vite. Part 1 hotel search is implemented; see [design](../docs/design.md).

## Responsibilities

- Part 1: accessible hotel-name input and Search button; plain labeled table with one row per offered stay; loading, no-results, and request-error states.
- Part 2, not yet implemented: simulated booking creation, history, cancellation, and deletion.
- Use backend IDs, fixed offered dates, statuses, and supplied amounts. Inputs/selections are temporary UI state; persistent records belong in SQLite behind FastAPI.
- Keep a readable layout on phone and desktop with keyboard focus and table headers. Images and elaborate mobile navigation are optional.

Source belongs in `src/`; planned travel HTTP helpers belong in `src/api/`. Use focused components/composables where useful. Add tests for changed behavior and browser checks for rendered search and each CRUD action. Rename the starter UI/package labels to `expedia-clone` during implementation, keeping package metadata/lockfile consistent without dependency upgrades.

## Commands

From `frontend/` with existing dependencies:

```bash
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
npm test
./node_modules/.bin/oxlint .
./node_modules/.bin/eslint .
npm run build
```

Use `npm ci` only for a needed, authorized setup; follow CHECK → TAKE ACTION → VERIFY. See [root setup](../README.md) for the declared Node version and backend startup. Existing `npm run lint` enables automatic fixes, so use the direct commands above for read-only verification.

Vite proxies `/api` to `http://127.0.0.1:8000`. Both services are required for integration checks. See [verification](../docs/verification.md).
