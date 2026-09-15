import { ref } from 'vue'
import { getUsers, getBookings, createBooking, cancelBooking, deleteBooking } from '../api/bookings.js'

export function useBookings() {
  const users = ref([])
  const userId = ref('')
  const bookings = ref([])
  const busy = ref(false)
  const historyLoading = ref(false)
  const historyError = ref('')
  const actionError = ref('')
  const message = ref('')
  let historyRequest = 0

  async function loadHistory() {
    const request = ++historyRequest
    bookings.value = []
    historyError.value = ''
    if (!userId.value) return
    historyLoading.value = true
    try {
      const data = await getBookings(userId.value)
      if (request === historyRequest) bookings.value = data
    } catch (error) {
      if (request === historyRequest) historyError.value = error.message
    } finally {
      if (request === historyRequest) historyLoading.value = false
    }
  }

  async function initialize() {
    busy.value = true
    actionError.value = ''
    try {
      users.value = await getUsers()
      userId.value = users.value[0]?.user_id || ''
      await loadHistory()
    } catch (error) {
      actionError.value = error.message
    } finally {
      busy.value = false
    }
  }

  async function selectTraveler() {
    message.value = ''
    actionError.value = ''
    await loadHistory()
  }

  async function mutate(action, successMessage) {
    if (busy.value) return
    message.value = ''
    actionError.value = ''
    if (!userId.value) {
      actionError.value = 'Select a traveler first.'
      return
    }
    busy.value = true
    try {
      await action()
      message.value = successMessage
      await loadHistory()
    } catch (error) {
      actionError.value = error.message
    } finally {
      busy.value = false
    }
  }

  return {
    users, userId, bookings, busy, historyLoading, historyError, actionError, message,
    initialize, loadHistory, selectTraveler,
    book: (tripId) => mutate(() => createBooking(userId.value, tripId), 'Booking saved. View it in booking history.'),
    cancel: (bookingId) => mutate(() => cancelBooking(bookingId, userId.value), 'Booking cancelled. The record remains in history.'),
    remove: (bookingId) => mutate(() => deleteBooking(bookingId, userId.value), 'Booking deleted.'),
  }
}
