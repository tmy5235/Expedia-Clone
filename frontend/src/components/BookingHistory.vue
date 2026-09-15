<script setup>
import { ref } from 'vue'

defineProps({
  bookings: { type: Array, required: true },
  busy: Boolean,
  loading: Boolean,
  error: { type: String, default: '' },
})
const emit = defineEmits(['cancel', 'remove', 'refresh'])
const pendingDelete = ref('')
const money = (cents) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(cents / 100)
function remove(bookingId) {
  pendingDelete.value = ''
  emit('remove', bookingId)
}
</script>

<template>
  <section aria-labelledby="history-heading">
    <h2 id="history-heading">Booking history</h2>
    <button type="button" :disabled="busy || loading" @click="emit('refresh')">Refresh history</button>
    <p v-if="loading" role="status">Loading booking history…</p>
    <p v-else-if="error" class="error" role="alert">{{ error }}</p>
    <p v-else-if="bookings.length === 0">No bookings for this traveler yet.</p>
    <div v-else class="table-wrapper">
      <table>
        <caption>Saved bookings for the selected traveler</caption>
        <thead><tr>
          <th scope="col">Booking ID</th><th scope="col">Hotel / stay</th>
          <th scope="col">Dates</th><th scope="col">Total</th><th scope="col">Booked on</th>
          <th scope="col">Status</th><th scope="col">Actions</th>
        </tr></thead>
        <tbody>
          <tr v-for="booking in bookings" :key="booking.booking_id">
            <td class="booking-id">{{ booking.booking_id }}</td>
            <td>{{ booking.hotel_name }}<br>{{ booking.trip_name }} ({{ booking.trip_id }})</td>
            <td>{{ booking.check_in }} to {{ booking.check_out }}</td>
            <td>{{ money(booking.total_cents) }}</td>
            <td>{{ booking.booked_on }}</td>
            <td>{{ booking.status }}</td>
            <td>
              <div class="actions">
                <button v-if="booking.status === 'confirmed'" :disabled="busy" :aria-label="`Cancel booking ${booking.booking_id}`" @click="emit('cancel', booking.booking_id)">Cancel</button>
                <button :disabled="busy" :aria-label="`Delete booking ${booking.booking_id}`" @click="pendingDelete = booking.booking_id">Delete</button>
              </div>
              <div v-if="pendingDelete === booking.booking_id" class="delete-confirmation">
                <p>Delete this booking permanently?</p>
                <button :disabled="busy" @click="remove(booking.booking_id)">Confirm delete</button>
                <button :disabled="busy" @click="pendingDelete = ''">Keep booking</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
