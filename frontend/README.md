# Hotel Finder Frontend

This Vue 3 interface uses the Composition API with `<script setup>` and Vite.
It provides local-first hotel discovery, saved hotels with simulated nightly data,
and a RAG assistant, plus a separate fictional hotel search and booking workflow.
FastAPI handles Geoapify and LLM requests; SQLite owns all persistent data.

## Live discovery

Visible brand: **Hotel Finder**. `App.vue` holds the small header and
discovery page. `BookingDemo.vue` preserves the original workflow and is loaded
only at `/?demo=booking`; there is no legacy demo control on the homepage. `discovery-landscape.svg`
is an original decorative hero illustration, not a photograph of returned hotels.

`HotelDiscovery.vue` renders the ZIP input and returned hotel list; `HotelMap.vue`
uses approved Leaflet 1.9.4 and keyless OSM tiles. `useDiscovery.js` shares one
provider place ID between list/marker selection and clears stale results.
`api/discovery.js` calls only the frozen backend discovery route. `useDiscovery.js`
first checks the backend local collection and falls back to discovery only after
a successful empty response. `api/localHotels.js` handles saved status and
Add/Remove actions. Saved rates and rooms carry a concise simulated-data disclosure;
Geoapify places have no real rates, ratings or availability. API keys stay on the backend.
See [Discovery design](../docs/assignment2-design.md) and
[verification](../docs/assignment2-verification.md).

## Saved-hotel assistant

`HotelAssistant.vue` renders **Compare saved hotels**, supporting records/SQL,
and saved conversation history. `useChat.js` coordinates backend requests and
collection-derived suggested questions; `api/chat.js` validates API responses.
`utils/chatPresentation.js` formats answers as safe text and readable lists.
Vue never runs SQL or calls the model provider directly. The backend validates
read-only queries and sends retrieved records to the model for the answer.

Save hotels first, then use a suggestion or ask about a saved ZIP and recorded
stay dates. Empty collections and missing dates receive guidance. The current
assistant compares available saved stays; it does not search the whole provider
inventory or make bookings. History persists in SQLite, not browser storage.
See [RAG verification and limitations](../docs/rag-context.md).

## Original booking workflow responsibilities

- Search for full or partial hotel names and display matching stays in a labeled table.
- Create an account, log in/out, restore the server session, and read the signed-in traveler's history from FastAPI.
- Create a booking from a search result, cancel it while retaining the history row, and delete a test booking after confirmation.
- Present clear loading, empty, success, validation, and request-error states.
- Keep only temporary interface state in Vue; never treat frontend state as persistent storage.
- Remain readable on phone and desktop with keyboard focus and accessible table headings.

The booking interface uses standard traveler and booking terminology. Its underlying
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

Search rates and daily counts come from the backend. `useSearch` clears stale responses when accounts change; `useAccount` coordinates authentication; `useBookings` coordinates saved booking actions. Set `EXPEDIA_API_TARGET` to use a different backend during isolated tests.

The daily rule uses `America/New_York`: the first three same-user, normalized-query searches return base price; the fourth and later return base × 1.20 once. The booking request includes the returned search ID so the backend can verify ownership and save the accepted total. Logging out clears account results and history.
