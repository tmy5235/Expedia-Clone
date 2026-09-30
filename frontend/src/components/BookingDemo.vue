<script setup>
import { onMounted, watch } from 'vue'
import BookingHistory from './BookingHistory.vue'
import ZipLookupPanel from './ZipLookupPanel.vue'
import { useBookings } from '../composables/useBookings.js'

import AccountPanel from './AccountPanel.vue'
import { useAccount } from '../composables/useAccount.js'
import { useSearch } from '../composables/useSearch.js'

const account = useAccount()
const { user, busy: accountBusy, error: accountError, message: accountMessage } = account
const { userId, bookings, busy, historyLoading, historyError, actionError, message,
  loadHistory, selectTraveler, book, cancel, remove } = useBookings()
const search = useSearch()
const { hotelName, searchedName, stays, error, hasSearched, isLoading, submitSearch } = search
onMounted(account.initialize)
watch(user, async (current) => {
  search.clear()
  userId.value = current?.user_id || ''
  await selectTraveler()
}, { flush: 'sync' })

const currencyFormatter = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 2,
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

</script>

<template>
  <section class="booking-demo" aria-label="Assignment 1 classroom demo">

    <h2>Fictional booking demonstration</h2>
    <p>Search the supplied sample stays by hotel name. These local classroom records are separate from live hotel discovery.</p>

    <AccountPanel :user="user" :busy="accountBusy || busy || isLoading" :error="accountError" :message="accountMessage"
      @submit="account.submit" @logout="account.logout" @retry="account.initialize" />
    <p v-if="busy" role="status">Saving booking…</p>
    <p v-if="actionError" class="error" role="alert">{{ actionError }}</p>
    <p v-if="message" role="status">{{ message }}</p>

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
          :disabled="isLoading || accountBusy"
          :aria-invalid="Boolean(error)"
        />
        <button type="submit" :disabled="isLoading || accountBusy">
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
        <p v-if="user">Matching searches today: {{ stays[0].search_count }} · America/New_York. Rates increase 20% from the fourth matching search.</p>
        <p v-else>Log in before searching to book a stay.</p>
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
                <td><button :disabled="busy || accountBusy || historyLoading || !userId" :aria-label="userId ? `Book stay ${stay.trip_id}` : `Log in to book stay ${stay.trip_id}`" @click="book(stay)">{{ userId ? 'Book stay' : 'Log in to book' }}</button></td>
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
    <ZipLookupPanel />
  </section>
</template>

<style scoped>
.booking-demo {
  width: min(100% - 2rem, 72rem);
  margin: 0 auto;
  padding: 3rem 0;
  color: #222;
}

:deep(h1) {
  margin: 0 0 0.5rem;
  font-size: 2rem;
}

:deep(h2) {
  margin: 2.5rem 0 0.5rem;
  font-size: 1.35rem;
}

:deep(p) {
  margin: 0.4rem 0;
}

:deep(form) {
  max-width: 42rem;
  margin-top: 2rem;
}

:deep(label) {
  display: block;
  margin-bottom: 0.4rem;
  font-weight: 700;
}

:deep(.search-row) {
  display: flex;
  gap: 0.5rem;
}

:deep(input), select {
  width: 100%;
  min-width: 0;
  padding: 0.7rem;
  border: 1px solid #777;
  border-radius: 0.25rem;
  background: #fff;
}

:deep(button) {
  padding: 0.7rem 1.25rem;
  border: 1px solid #1558b0;
  border-radius: 0.25rem;
  color: #fff;
  background: #1668e3;
  cursor: pointer;
}

:deep(button):disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

:deep(input):focus-visible,
:deep(select):focus-visible,
:deep(button):focus-visible {
  outline: 3px solid #8bb8ff;
  outline-offset: 2px;
}

:deep(.message) {
  margin-top: 1.25rem;
}

:deep(.error) {
  color: #a11;
}

:deep(.table-wrapper) {
  margin-top: 1rem;
  overflow-x: auto;
}

:deep(table) {
  width: 100%;
  min-width: 62rem;
  border-collapse: collapse;
  background: #fff;
}

:deep(caption) {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
}

:deep(th),
:deep(td) {
  padding: 0.75rem;
  border: 1px solid #bbb;
  text-align: left;
  vertical-align: top;
}

:deep(th) {
  background: #eee;
  font-weight: 700;
}

:deep(select) { max-width: 28rem; font: inherit; }
:deep(.actions) { display: flex; gap: 0.5rem; flex-wrap: wrap; }
:deep(.booking-id) { overflow-wrap: anywhere; min-width: 9rem; max-width: 13rem; }
:deep(.delete-confirmation) { min-width: 15rem; margin-top: 0.75rem; }
:deep(.delete-confirmation) button { margin: 0.25rem; }

@media (max-width: 35rem) {
  .booking-demo {
    padding-top: 2rem;
  }

  :deep(.search-row) {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
