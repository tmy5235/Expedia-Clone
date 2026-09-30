<script setup>
import { useZipLookup } from '../composables/useZipLookup.js'

const { postcode, submittedPostcode, location, error, isLoading, lookup } = useZipLookup()
</script>

<template>
  <section class="zip-panel" aria-labelledby="zip-heading">
    <h2 id="zip-heading">ZIP lookup</h2>
    <p>Enter a U.S. ZIP code to find its location.</p>
    <form class="zip-form" novalidate @submit.prevent="lookup">
      <label for="zip-code">ZIP code</label>
      <div class="search-row">
        <input id="zip-code" v-model="postcode" name="postcode" type="text"
          inputmode="numeric" autocomplete="postal-code" :disabled="isLoading"
          :aria-invalid="Boolean(error)" aria-describedby="zip-help" />
        <button type="submit" :disabled="isLoading">Look up ZIP</button>
      </div>
      <p id="zip-help">Use five digits, including any leading zero.</p>
    </form>
    <div aria-live="polite" :aria-busy="isLoading">
      <p v-if="isLoading" role="status">Looking up ZIP {{ submittedPostcode }}…</p>
      <p v-else-if="error" class="error" role="alert">{{ error }}</p>
      <div v-else-if="location" class="table-wrapper">
        <table class="zip-results">
          <caption>Location returned for ZIP {{ location.postcode }}</caption>
          <thead>
            <tr>
              <th scope="col">ZIP code</th><th scope="col">Country</th>
              <th scope="col">Locality</th><th scope="col">Latitude</th>
              <th scope="col">Longitude</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{{ location.postcode }}</td><td>{{ location.country_code.toUpperCase() }}</td>
              <td>{{ location.locality || 'Not provided' }}</td>
              <td>{{ location.latitude }}</td><td>{{ location.longitude }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<style scoped>
.zip-panel {
  margin-top: 2rem;
  padding: 1.25rem;
  border: 1px solid #cdd9eb;
  border-radius: 0.5rem;
  background: #f4f7fc;
}
h2 { margin-top: 0; margin-bottom: 1rem; }
p { margin: 0.75rem 0 0; }
.zip-form { max-width: 28rem; margin-top: 1rem; }
.zip-form button { white-space: nowrap; }
#zip-help { font-size: 0.875rem; color: #4a5568; }
.zip-results { min-width: 34rem; }
.zip-results caption {
  position: static;
  width: auto;
  height: auto;
  clip: auto;
  white-space: normal;
  text-align: left;
  padding-bottom: 0.75rem;
  font-weight: 700;
}
</style>
