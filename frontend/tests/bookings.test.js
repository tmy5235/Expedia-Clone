import assert from 'node:assert/strict'
import test from 'node:test'
import { createBooking, cancelBooking, deleteBooking, getBookings } from '../src/api/bookings.js'
import { useBookings } from '../src/composables/useBookings.js'

const json = (value, status = 200) => new Response(JSON.stringify(value), { status })

test('booking requests use backend CRUD with traveler and stay IDs', async (context) => {
  const calls = []
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push([url, options])
    if (options?.method === 'DELETE') return new Response(null, { status: 204 })
    return json(options ? { booking_id: 'B-new' } : [])
  })
  await getBookings('U006')
  await createBooking('U006', 'T001', 4)
  await cancelBooking('B-new', 'U006')
  await deleteBooking('B-new', 'U006')
  assert.equal(calls[0][0], '/api/bookings?user_id=U006')
  assert.equal(calls[1][1].method, 'POST')
  assert.deepEqual(JSON.parse(calls[1][1].body), { user_id: 'U006', trip_id: 'T001', search_id: 4 })
  assert.equal(calls[2][1].method, 'PATCH')
  assert.deepEqual(JSON.parse(calls[2][1].body), { user_id: 'U006', status: 'cancelled' })
  assert.equal(calls[3][0], '/api/bookings/B-new?user_id=U006')
  assert.equal(calls[3][1].method, 'DELETE')
})

test('reports API, validation, connection, and invalid-response errors clearly', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json({ detail: 'Stay not found.' }, 404))
  await assert.rejects(createBooking('U001', 'missing'), /Stay not found/)
  mock.mock.mockImplementation(async () => json({ detail: [{ msg: 'invalid' }] }, 422))
  await assert.rejects(createBooking('', ''), /could not be completed/)
  mock.mock.mockImplementation(async () => { throw new Error('offline') })
  await assert.rejects(getBookings('U001'), /Unable to reach/)
  mock.mock.mockImplementation(async () => json({}))
  await assert.rejects(getBookings('U001'), /invalid response/)
})

test('mutation reloads saved history and failed mutation preserves history', async (context) => {
  let saved = []
  let fail = false
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    if (options) {
      if (fail) return json({ detail: 'Database unavailable.' }, 503)
      saved = [{ booking_id: 'B-new', status: 'confirmed' }]
      return json(saved[0], 201)
    }
    return json(saved)
  })
  const state = useBookings()
  state.userId.value = 'U006'
  await state.loadHistory()
  assert.deepEqual(state.bookings.value, [])
  await state.book({ trip_id: 'T001', search_id: 4 })
  assert.equal(state.bookings.value[0].booking_id, 'B-new')
  assert.equal(state.message.value, 'Booking saved. View it in booking history.')
  fail = true
  await state.cancel('B-new')
  assert.match(state.actionError.value, /Database unavailable/)
  assert.equal(state.message.value, '')
  assert.equal(state.bookings.value[0].status, 'confirmed')
  assert.equal(state.busy.value, false)
})

test('outdated history responses cannot replace the selected traveler history', async (context) => {
  const resolvers = []
  context.mock.method(globalThis, 'fetch', () => new Promise((resolve) => resolvers.push(resolve)))
  const state = useBookings()
  state.userId.value = 'U001'
  const first = state.loadHistory()
  state.userId.value = 'U006'
  const second = state.loadHistory()
  resolvers[1](json([]))
  await second
  resolvers[0](json([{ booking_id: 'B001' }]))
  await first
  assert.deepEqual(state.bookings.value, [])
  assert.equal(state.historyLoading.value, false)
})

test('history refresh failures show an error while preserving successful save notice', async (context) => {
  context.mock.method(globalThis, 'fetch', async (_url, options) => options ? json({ booking_id: 'B-new' }, 201) : json({ detail: 'History unavailable.' }, 503))
  const state = useBookings()
  state.userId.value = 'U006'
  await state.book({ trip_id: 'T001', search_id: 4 })
  assert.equal(state.message.value, 'Booking saved. View it in booking history.')
  assert.match(state.historyError.value, /History unavailable/)
  assert.equal(state.busy.value, false)
})
