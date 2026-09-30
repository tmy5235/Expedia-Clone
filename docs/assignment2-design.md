# Hotel Finder — discovery API and MVC design

## MVC responsibilities

The visible app is **Hotel Finder**. `App.vue` contains the header and
discovery page; the original booking/account/coordinate UI is lazy-loaded through
`BookingDemo.vue` at `/?demo=booking`. The homepage omits the old demo control and
keeps the discovery interface focused on ZIP search. The legacy backend/data are
unchanged. Search-location coordinates are disclosed on demand and hotel coordinates
appear on the selected card, reducing clutter without inventing or dropping data.

- Model: `app/schemas.py` defines external place/center/response data. Existing
  `database.py` and migrations own SQLite; no database migration or persistence
  is added for discovery.
- Controllers: `controllers/locations.py` owns credential-safe provider transport
  and exact ZIP resolution. `controllers/discovery.py` sequences geocoding and
  Places, applies radius/limit rules, and normalizes provider fields. Thin FastAPI
  routes validate query input and translate typed failures into safe HTTP errors.
- View: `useDiscovery.js` owns transient request/selection state; `HotelDiscovery.vue`
  renders inputs/list/feedback; `HotelMap.vue` presents Leaflet layers and emits a
  selected provider ID. Both representations use that same ID. API payloads are
  checked in `api/discovery.js`. Vue contains no pricing or persistence logic.

## API

`GET /api/discovery/hotels?postcode=00501` is anonymous and does not enter the
original account-based hotel-name search history. Exactly five ASCII digits
are required. Leading zeros remain intact. Successful responses are not cached
by the local endpoint (`Cache-Control: no-store`).

1. Resolve the requested postcode through the existing Geoapify geocoding flow.
   Require exact postcode, U.S. country, postcode result type, and valid finite
   coordinates. An unresolved or mismatched response never triggers Places.
2. Call `/v2/places` with `categories=accommodation.hotel`,
   `filter=circle:longitude,latitude,5000`, matching proximity bias, and `limit=20`.
   No pagination, retries, IP location, or device geolocation.
3. Read GeoJSON Point coordinates, `properties.place_id`, optional `name`, and
   optional `formatted` address. Preserve provider order. Deduplicate IDs and
   omit records lacking IDs/valid points or outside the 5 km great-circle radius.
   Report all omissions; missing names/addresses remain null, with honest UI labels.

Response fields:

| Field | Meaning |
| --- | --- |
| `provider` | Always `geoapify` |
| `center` | Verified `postcode`, `country_code`, latitude/longitude, optional locality |
| `radius_meters` | 5000 |
| `result_limit` | 20; one page only |
| `limit_reached` | Provider returned at least 20 features; additional places may exist |
| `omitted_count` | Records excluded for invalid/missing ID/point, duplicates, radius, or page limit |
| `hotels` | `place_id`, optional `name`/`address`, and numeric `latitude`/`longitude` |

This external place representation deliberately has no nightly rate, trip ID,
availability, or reservation. It has no persistent shortlist or saved-place table.

| Outcome | HTTP/UI |
| --- | --- |
| Results or genuinely empty Places feature list | 200; list/map or clear no-results message with center map |
| Invalid/missing ZIP | 422; client also validates before sending |
| Unresolved/mismatched U.S. ZIP | 404; distinct message |
| Missing configuration | 503; safe configuration feedback |
| Provider quota/rate limit at either stage | 429; try-later feedback, no retry loop |
| Provider HTTP/network/malformed response | 502; failure, never successful empty results |

Each upstream operation has existing 10-second connect/read/write/pool timeouts;
the browser gives up after 30 seconds. A browser abort does not guarantee that
an in-progress synchronous upstream request stops instantly. All errors exclude
provider bodies, credentials, and raw transport URLs. The key remains in `.env`
and backend process memory. Existing ZIP routes preserve their prior error contract.

## Map and accessibility

Numbered native list buttons and numbered Leaflet markers share selection.
Markers support Enter and Space, expose accessible names/pressed states, and
open a text-only popup. Names and addresses are never inserted as provider HTML.
The map shows a 5 km circle and center point; panning does not issue a search.
The map is removed on unmount and resized when its container changes. The list
stacks above the map on narrow screens. Tile errors show a separate warning while
the hotel list remains usable. Tile availability is independent of Places success.

Tiles: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`. Visible OSM attribution
remains on the map, and Geoapify/OSM source links remain below discovery. No tile
credential, geocoding/Places key in the browser, bulk tile download, offline map,
or claim of exhaustive hotel coverage. Intended for modest local classroom use.
