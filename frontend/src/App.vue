<script setup>
import { onMounted, ref } from 'vue'
import BookingHistory from './components/BookingHistory.vue'
import { useBookings } from './composables/useBookings.js'

import { searchStays } from './api/stays'

const {
  users, userId, bookings, busy, historyLoading, historyError, actionError, message,
  initialize, loadHistory, selectTraveler, book, cancel, remove,
} = useBookings()
onMounted(initialize)

const hotelName = ref('')
const searchedName = ref('')
const stays = ref([])
const error = ref('')
const hasSearched = ref(false)
const isLoading = ref(false)

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
})

function formatCurrency(cents) {
  return currencyFormatter.format(cents / 100)
}

function formatDate(value) {
  return dateFormatter.format(new Date(`${value}T00:00:00`))
}

function formatTravelerName(value) {
  return value.replace(/^Demo\s+/i, '')
}

async function submitSearch() {
  const query = hotelName.value.trim()
  error.value = ''

  if (!query) {
    stays.value = []
    hasSearched.value = false
    error.value = 'Enter a hotel name to search.'
    return
  }

  isLoading.value = true
  searchedName.value = query
  stays.value = []

  try {
    stays.value = await searchStays(query)
    hasSearched.value = true
  } catch (searchError) {
    hasSearched.value = false
    error.value = searchError instanceof Error ? searchError.message : 'Search failed. Try again.'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <main>
    <h1>Expedia Clone</h1>
    <p>Search for available stays by hotel name and manage your bookings.</p>

    <section aria-labelledby="traveler-heading">
      <h2 id="traveler-heading">Traveler</h2>
      <label for="traveler">Select a traveler</label>
      <select id="traveler" v-model="userId" :disabled="busy || historyLoading" @change="selectTraveler">
        <option value="" disabled>Select a traveler</option>
        <option v-for="user in users" :key="user.user_id" :value="user.user_id">{{ formatTravelerName(user.display_name) }}</option>
      </select>
      <button v-if="users.length === 0 && !busy" @click="initialize">Reload travelers</button>
      <p v-if="busy" role="status">Saving or loading booking data…</p>
      <p v-if="actionError" class="error" role="alert">{{ actionError }}</p>
      <p v-if="message" role="status">{{ message }}</p>
    </section>

    <form @submit.prevent="submitSearch">
      <label for="hotel-name">Hotel name</label>
      <div class="search-row">
        <input
          id="hotel-name"
          v-model="hotelName"
          name="hotel_name"
          type="search"
          placeholder="Harbor Lantern Hotel"
          autocomplete="off"
          :disabled="isLoading"
          :aria-invalid="Boolean(error)"
        />
        <button type="submit" :disabled="isLoading">
          {{ isLoading ? 'Searching…' : 'Search' }}
        </button>
      </div>
    </form>

    <p v-if="isLoading" class="message" role="status">Searching available stays…</p>
    <p v-else-if="error" class="message error" role="alert">{{ error }}</p>

    <section v-else-if="hasSearched" aria-live="polite">
      <h2>Search results</h2>

      <p v-if="stays.length === 0" class="message">
        No hotels matched “{{ searchedName }}”.
      </p>

      <template v-else>
        <p>{{ stays.length }} {{ stays.length === 1 ? 'stay' : 'stays' }} found.</p>

        <div class="table-wrapper">
          <table>
            <caption>
              Available stays matching {{ searchedName }}
            </caption>
            <thead>
              <tr>
                <th scope="col">Hotel</th>
                <th scope="col">Location</th>
                <th scope="col">Stay</th>
                <th scope="col">Check-in</th>
                <th scope="col">Check-out</th>
                <th scope="col">Nights</th>
                <th scope="col">Nightly rate</th>
                <th scope="col">Total</th>
                <th scope="col">Booking</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="stay in stays" :key="stay.trip_id">
                <td>{{ stay.hotel_name }}</td>
                <td>{{ stay.city }}, {{ stay.state }}</td>
                <td>{{ stay.trip_name }} ({{ stay.trip_id }})</td>
                <td>{{ formatDate(stay.check_in) }}</td>
                <td>{{ formatDate(stay.check_out) }}</td>
                <td>{{ stay.nights }}</td>
                <td>{{ formatCurrency(stay.nightly_rate_cents) }}</td>
                <td>{{ formatCurrency(stay.total_cents) }}</td>
                <td><button :disabled="busy || historyLoading || !userId" :aria-label="`Book stay ${stay.trip_id}`" @click="book(stay.trip_id)">Book stay</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </section>
    <BookingHistory
      v-if="userId"
      :key="userId"
      :bookings="bookings"
      :busy="busy"
      :loading="historyLoading"
      :error="historyError"
      @refresh="loadHistory"
      @cancel="cancel"
      @remove="remove"
    />
  </main>
</template>

<style>
main {
  width: min(100% - 2rem, 72rem);
  margin: 0 auto;
  padding: 3rem 0;
  color: #222;
}

h1 {
  margin: 0 0 0.5rem;
  font-size: 2rem;
}

h2 {
  margin: 2.5rem 0 0.5rem;
  font-size: 1.35rem;
}

p {
  margin: 0.4rem 0;
}

form {
  max-width: 42rem;
  margin-top: 2rem;
}

label {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 700;
}

.search-row {
  display: flex;
  gap: 0.5rem;
}

input, select {
  width: 100%;
  min-width: 0;
  padding: 0.7rem;
  border: 1px solid #777;
  border-radius: 0.25rem;
  background: #fff;
}

button {
  padding: 0.7rem 1.25rem;
  border: 1px solid #1558b0;
  border-radius: 0.25rem;
  color: #fff;
  background: #1668e3;
  cursor: pointer;
}

button:disabled {
  cursor: wait;
  opacity: 0.65;
}

input:focus-visible,
select:focus-visible,
button:focus-visible {
  outline: 3px solid #8bb8ff;
  outline-offset: 2px;
}

.message {
  margin-top: 1.25rem;
}

.error {
  color: #a11;
}

.table-wrapper {
  margin-top: 1rem;
  overflow-x: auto;
}

table {
  width: 100%;
  min-width: 62rem;
  border-collapse: collapse;
  background: #fff;
}

caption {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

th,
td {
  padding: 0.75rem;
  border: 1px solid #bbb;
  text-align: left;
  vertical-align: top;
}

th {
  background: #eee;
  font-weight: 700;
}

select { max-width: 28rem; font: inherit; }
.actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.booking-id { overflow-wrap: anywhere; min-width: 9rem; max-width: 13rem; }
.delete-confirmation { min-width: 15rem; margin-top: 0.75rem; }
.delete-confirmation button { margin: 0.25rem; }

@media (max-width: 35rem) {
  main {
    padding-top: 2rem;
  }

  .search-row {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
