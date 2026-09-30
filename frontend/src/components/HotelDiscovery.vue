<script setup>
import { nextTick, onBeforeUnmount, ref } from 'vue'
import HotelMap from './HotelMap.vue'
import { useDiscovery } from '../composables/useDiscovery.js'

const { postcode, result, selectedId, selectedHotel, status, error, isLoading, search, select, clear } = useDiscovery()
const list = ref(null)

async function selectFromMap(placeId) {
  select(placeId)
  await nextTick()
  list.value?.querySelector('[aria-pressed="true"]')?.scrollIntoView({ block: 'nearest', behavior: 'auto' })
}
onBeforeUnmount(clear)
</script>

<template>
  <section class="discovery" aria-label="Hotel discovery">
    <div class="hero">
      <h1>Find somewhere to stay.</h1>
    </div>

    <div class="discovery-content">
      <form id="hotel-search" class="search-card" novalidate @submit.prevent="search">
        <div class="search-card-heading">
          <span class="search-category"><svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 18V9m18 9V9M3 15h18M6 11V6h12v5M3 11h18v4H3zM9 6v5m6-5v5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" /></svg>Hotels</span>
          <span class="search-scope">Explore within 5 km</span>
        </div>
        <div class="search-controls">
          <div class="zip-field">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z" stroke="currentColor" stroke-width="1.7"/><circle cx="12" cy="10" r="2.4" stroke="currentColor" stroke-width="1.7"/></svg>
            <div>
              <label for="discovery-zip">Where to? <span>U.S. ZIP code</span></label>
              <input id="discovery-zip" v-model="postcode" type="text" inputmode="numeric" autocomplete="postal-code" placeholder="Enter a five-digit ZIP"
                aria-label="U.S. ZIP code" :disabled="isLoading" :aria-invalid="status === 'invalid'" aria-describedby="discovery-help discovery-feedback" />
            </div>
          </div>
          <button class="search-button" :disabled="isLoading" type="submit">{{ isLoading ? 'Searching…' : 'Find hotels' }}<span v-if="!isLoading" aria-hidden="true">→</span></button>
        </div>
        <p id="discovery-help" class="search-help">Five digits, including leading zeros. No sign-in needed.</p>
      </form>

      <div id="discovery-feedback" aria-live="polite" :aria-busy="isLoading">
        <p v-if="isLoading" class="feedback" role="status">Finding hotels near ZIP {{ postcode }}…</p>
        <p v-else-if="error" class="feedback error" role="alert">{{ error }}</p>
      </div>

      <div v-if="status === 'idle'" class="welcome">
        <span class="welcome-icon" aria-hidden="true">↗</span>
        <div><h2>A place to start exploring.</h2><p>Enter a ZIP code to see nearby hotels, together on one map.</p></div>
      </div>

      <section v-if="result" class="results" aria-labelledby="results-heading">
        <div class="results-heading">
          <div><p class="section-eyebrow">YOUR NEXT STOP</p><h2 id="results-heading">Hotels near {{ result.center.locality || result.center.postcode }}</h2></div>
          <span class="result-count">{{ result.hotels.length }} {{ result.hotels.length === 1 ? 'hotel' : 'hotels' }} returned</span>
        </div>
        <p class="result-context">Within 5 km of the returned ZIP {{ result.center.postcode }} location.</p>
        <p class="result-limit">Up to {{ result.result_limit }} places per search; coverage varies. {{ result.limit_reached ? 'Result limit reached—more hotels may exist.' : 'Results are not an exhaustive hotel inventory.' }}</p>
        <p v-if="result.omitted_count" class="feedback">{{ result.omitted_count }} provider {{ result.omitted_count === 1 ? 'record was' : 'records were' }} omitted because of missing or invalid location/ID data, duplicates, or the search limits.</p>
        <p v-if="status === 'empty'" class="feedback" role="status">{{ result.omitted_count ? 'No displayable hotels were returned for this search.' : 'No hotels were returned within 5 km of this ZIP location.' }} Try another ZIP code.</p>
        <p class="selection-status" role="status">{{ selectedHotel ? `Selected: ${selectedHotel.name || 'Name not provided'}` : 'Select a hotel or map pin to take a closer look.' }}</p>
        <div class="discovery-results" :class="{ 'map-only': !result.hotels.length }">
          <ol v-if="result.hotels.length" ref="list" class="hotel-list" aria-label="Hotels returned by Geoapify">
            <li v-for="(hotel, index) in result.hotels" :key="hotel.place_id">
              <button type="button" class="hotel-card" :aria-pressed="selectedId === hotel.place_id"
                :aria-label="`Show hotel ${index + 1} on map: ${hotel.name || 'Name not provided'}`" @click="select(hotel.place_id)">
                <span class="number">{{ index + 1 }}</span>
                <span class="hotel-information">
                  <strong>{{ hotel.name || 'Name not provided' }}</strong>
                  <span class="hotel-address">{{ hotel.address || 'Address not provided' }}</span>
                  <span v-if="selectedId === hotel.place_id" class="hotel-coordinates">{{ hotel.latitude.toFixed(5) }}, {{ hotel.longitude.toFixed(5) }}</span>
                  <span class="selection-label">{{ selectedId === hotel.place_id ? 'Selected on map' : 'View on map' }} <span aria-hidden="true">↗</span></span>
                </span>
              </button>
            </li>
          </ol>
          <HotelMap :key="result.center.postcode" :result="result" :selected-id="selectedId" @select="selectFromMap" />
        </div>
        <details class="location-detail"><summary>Search location details</summary><p>ZIP {{ result.center.postcode }}, US · {{ result.center.locality || 'Locality not provided' }} · {{ result.center.latitude.toFixed(5) }}, {{ result.center.longitude.toFixed(5) }}</p></details>
      </section>

      <footer id="about-search" class="discovery-footer">
        <div><h2>Assignment 2.1 · IST 402</h2><p>Searches use a 5 km circle around the returned ZIP location, not your device location or the ZIP boundary. Hotel locations only—prices, ratings, availability, and reservations aren’t provided.</p></div>
        <p class="attribution">Powered by <a href="https://www.geoapify.com/">Geoapify</a><br>© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors</p>
      </footer>
    </div>
  </section>
</template>

<style scoped>
.hero { padding: 3.6rem 1.5rem 11rem; text-align: center; background: #d3e5e6 url('../assets/discovery-landscape.svg') center bottom / cover no-repeat; color: #193e42; }
h1 { font-family: Georgia, 'Times New Roman', serif; font-weight: 400; font-size: clamp(2.35rem, 4.2vw, 4rem); letter-spacing: -0.035em; line-height: 1.12; margin: 0; }
.discovery-content { width: min(100% - 3rem, 74rem); margin: 0 auto; }
.search-card { position: relative; margin: -4.5rem 0 0; background: white; border: 1px solid #d8e1e0; border-radius: 18px; box-shadow: 0 7px 24px #17383b0b; scroll-margin-top: 1rem; }
.search-card-heading { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #e8eceb; padding: 1.2rem 1.65rem; }
.search-category { font-size: 0.95rem; font-weight: 700; display: flex; gap: 0.7rem; align-items: center; color: #215b60; }
.search-category svg { width: 25px; height: 25px; }
.search-scope { font-size: 0.78rem; color: #65787a; }
.search-controls { display: flex; gap: 1rem; padding: 1.35rem 1.65rem 0; }
.zip-field { flex: 1; display: flex; align-items: center; gap: 0.9rem; border: 1px solid #aab9ba; border-radius: 10px; padding: 0.8rem 1rem; min-width: 0; }
.zip-field:focus-within { border-color: #215b60; outline: 2px solid #b67d1a; outline-offset: 3px; }
.zip-field > svg { width: 25px; height: 25px; flex-shrink: 0; }
.zip-field > div { flex: 1; min-width: 0; }
.zip-field label { font-size: 0.72rem; color: #5b7175; display: block; }
.zip-field label span { margin-left: 0.5rem; }
.zip-field input { border: 0; outline-offset: 2px; background: transparent; color: #183840; font-size: 1.1rem; width: 100%; min-width: 0; padding: 0.25rem 0 0; }
.zip-field input:focus-visible { outline: none; }
.search-button { border: 0; background: #185e65; color: white; border-radius: 10px; padding: 1rem 1.65rem; font-weight: 650; display: flex; align-items: center; justify-content: center; gap: 1.5rem; white-space: nowrap; transition: background 120ms; }
.search-button:hover:not(:disabled) { background: #11494f; }
.search-button span { font-size: 1.3rem; font-weight: 400; }
.search-help { padding: 0.8rem 1.65rem 1.2rem; font-size: 0.73rem; color: #6c7c7f; }
.feedback { padding: 1rem 1.2rem; margin-top: 1.25rem; background: #f0f5f4; border-radius: 10px; line-height: 1.5; }
.error { color: #972e28; background: #fff0ed; }
.welcome { display: flex; gap: 1.25rem; align-items: center; background: #f6f8f6; border-radius: 14px; padding: 2rem; margin: 2rem 0; }
.welcome-icon { color: #326967; font-size: 2rem; width: 3rem; height: 3rem; display: grid; place-items: center; background: #e5eeea; border-radius: 50%; flex-shrink: 0; }
.welcome h2 { font-family: Georgia, serif; font-weight: 400; font-size: 1.6rem; margin: 0 0 0.45rem; }
.welcome p { color: #607477; font-size: 0.88rem; line-height: 1.6; }
.results { padding-top: 2rem; }
.results-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
.section-eyebrow { font-size: 0.65rem; letter-spacing: 0.14em; font-weight: 700; color: #637b7b; margin-bottom: 0.5rem; }
.results-heading h2 { font-family: Georgia, serif; font-weight: 400; font-size: 2rem; margin: 0; line-height: 1.2; }
.result-count { flex-shrink: 0; font-size: 0.75rem; font-weight: 650; color: #345f5c; background: #eef4f0; border-radius: 20px; padding: 0.5rem 0.85rem; }
.result-context { font-size: 0.86rem; color: #526c6e; margin-top: 0.65rem; }
.result-limit { font-size: 0.74rem; color: #65787a; margin-top: 0.45rem; line-height: 1.6; }
.selection-status { font-size: 0.8rem; color: #4a6267; margin: 1.35rem 0 0.8rem; min-height: 1.2rem; }
.discovery-results { display: grid; grid-template-columns: minmax(17rem, 0.78fr) minmax(0, 1.4fr); gap: 1.1rem; align-items: start; }
.map-only { grid-template-columns: 1fr; }
.hotel-list { list-style: none; padding: 3px; margin: -3px; max-height: 30rem; overflow-y: auto; }
.hotel-list li + li { margin-top: 0.7rem; }
.hotel-card { display: flex; gap: 0.8rem; width: 100%; text-align: left; padding: 1.15rem; border: 1px solid #dde5e2; background: #fff; color: #1c3c40; border-radius: 12px; }
.hotel-card:hover { background: #f7faf8; border-color: #95b4ad; }
.hotel-card[aria-pressed='true'] { border-color: #33756e; background: #f0f7f3; box-shadow: inset 3px 0 #33756e; }
.number { flex-shrink: 0; display: grid; place-items: center; width: 1.6rem; height: 1.6rem; border-radius: 50%; background: #ecf2ef; color: #3f6c65; font-size: 0.75rem; font-weight: 750; }
.hotel-card[aria-pressed='true'] .number { color: white; background: #276b64; }
.hotel-information { display: block; min-width: 0; }
.hotel-information strong { font-size: 0.9rem; line-height: 1.6; }
.hotel-address, .hotel-coordinates, .selection-label { display: block; margin-top: 0.5rem; font-size: 0.75rem; line-height: 1.65; }
.hotel-address { color: #647677; }
.hotel-coordinates { color: #657a79; font-size: 0.7rem; }
.selection-label { color: #21635d; font-weight: 650; }
.selection-label span { padding-left: 0.35rem; }
.location-detail { margin-top: 0.7rem; color: #647a79; font-size: 0.75rem; line-height: 1.7; }
.location-detail summary { cursor: pointer; width: fit-content; }
.location-detail p { padding-top: 0.5rem; }
.discovery-footer { display: flex; justify-content: space-between; gap: 3rem; padding: 2rem 0 1.75rem; margin-top: 1.5rem; border-top: 1px solid #e6ebe8; scroll-margin-top: 2rem; }
.discovery-footer h2 { font-size: 0.85rem; font-weight: 650; margin: 0 0 0.6rem; }
.discovery-footer p { max-width: 44rem; font-size: 0.73rem; line-height: 1.85; color: #687b7c; }
.discovery-footer .attribution { flex-shrink: 0; text-align: right; }
.discovery-footer a { color: #42645f; text-underline-offset: 3px; }
@media (max-width: 48rem) {
  .discovery-results { grid-template-columns: 1fr; }
  .hotel-list { max-height: 22rem; }
  .hero { padding-top: 3rem; }
  .results-heading h2 { font-size: 1.7rem; }
}
@media (max-width: 40rem) {
  .discovery-content { width: calc(100% - 2rem); }
  .hero { padding: 2.5rem 1rem 10rem; }
  .search-card-heading { padding: 1rem; }
  .search-controls { padding: 1rem 1rem 0; flex-direction: column; gap: 0.65rem; }
  .search-button { padding: 0.8rem 1rem; }
  .search-help { padding: 0.7rem 1rem 1rem; font-size: 0.68rem; }
  .welcome { padding: 1.3rem; gap: 0.8rem; }
  .welcome h2 { font-size: 1.25rem; }
  .welcome p { font-size: 0.8rem; }
  .results-heading { align-items: start; }
  .result-count { font-size: 0.65rem; padding: 0.45rem 0.6rem; }
  .discovery-footer { flex-direction: column; gap: 1rem; }
  .discovery-footer .attribution { text-align: left; }
}
</style>
