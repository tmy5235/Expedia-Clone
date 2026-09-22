async function request(path, options, expectsArray = false) {
  let response
  try {
    response = await fetch(`/api${path}`, options)
  } catch {
    throw new Error('Unable to reach the booking service. Please try again.')
  }
  if (response.status === 204 && response.ok) return null
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : 'The booking request could not be completed.')
  }
  if (expectsArray ? !Array.isArray(data) : !data?.booking_id) {
    throw new Error('The booking service returned an invalid response.')
  }
  return data
}

export const getBookings = (userId) => request(`/bookings?${new URLSearchParams({ user_id: userId })}`, undefined, true)
export const createBooking = (userId, tripId, searchId) => request('/bookings', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId, trip_id: tripId, search_id: searchId }),
})
export const cancelBooking = (bookingId, userId) => request(`/bookings/${encodeURIComponent(bookingId)}`, {
  method: 'PATCH',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: userId, status: 'cancelled' }),
})
export const deleteBooking = (bookingId, userId) => request(`/bookings/${encodeURIComponent(bookingId)}?${new URLSearchParams({ user_id: userId })}`, { method: 'DELETE' })
