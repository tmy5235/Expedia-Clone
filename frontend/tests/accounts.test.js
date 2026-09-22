import assert from 'node:assert/strict'
import test from 'node:test'
import { useAccount } from '../src/composables/useAccount.js'
import { useSearch } from '../src/composables/useSearch.js'
import { useBookings } from '../src/composables/useBookings.js'

const json = (value, status = 200) => new Response(JSON.stringify(value), { status })
const user = { user_id: 'U-new', username: 'user_a' }
const credentials = { username: 'user_a', password: 'made-up-demo' }

test('account creation, login, session restoration and logout use the server', async (context) => {
  let signedIn = null
  const calls = []
  context.mock.method(globalThis, 'fetch', async (url, options) => {
    calls.push([url, options])
    if (url.endsWith('login')) signedIn = user
    if (url.endsWith('logout')) { signedIn = null; return new Response(null, { status: 204 }) }
    return json(url.endsWith('session') ? signedIn : user)
  })
  const account = useAccount()
  await account.initialize()
  assert.equal(account.user.value, null)
  await account.submit(credentials, true)
  assert.match(account.message.value, /Account created/)
  assert.equal(account.user.value, null)
  await account.submit(credentials, false)
  assert.deepEqual(account.user.value, user)
  assert.deepEqual(JSON.parse(calls[2][1].body), credentials)
  const restored = useAccount()
  await restored.initialize()
  assert.deepEqual(restored.user.value, user)
  await account.logout()
  assert.equal(account.user.value, null)
  assert.match(account.message.value, /logged out/)
})

test('duplicate accounts, bad login and offline errors are clear; failed login clears user', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json({ detail: 'That username is already taken.' }, 409))
  const state = useAccount()
  await state.submit(credentials, true)
  assert.match(state.error.value, /already taken/)
  state.user.value = user
  mock.mock.mockImplementation(async () => json({ detail: 'Incorrect username or password.' }, 401))
  await state.submit(credentials, false)
  assert.equal(state.user.value, null)
  assert.match(state.error.value, /Incorrect/)
  assert.equal(state.busy.value, false)
  mock.mock.mockImplementation(async () => { throw new Error('offline') })
  await state.initialize()
  assert.match(state.error.value, /Unable to reach/)
})

test('failed logout retains current account until the server confirms logout', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => json({ detail: 'Database unavailable.' }, 503))
  const state = useAccount()
  state.user.value = user
  await state.logout()
  assert.deepEqual(state.user.value, user)
  assert.match(state.error.value, /Database unavailable/)
})

test('search submits once per action and displays server price without calculating', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json([{ nightly_rate_cents: 12000, search_count: 4 }]))
  const state = useSearch()
  state.hotelName.value = ' Valley Trail '
  await Promise.all([state.submitSearch(), state.submitSearch()])
  assert.equal(mock.mock.callCount(), 1)
  assert.equal(state.stays.value[0].nightly_rate_cents, 12000)
  state.hotelName.value = ' '
  await state.submitSearch()
  assert.equal(mock.mock.callCount(), 1)
  assert.match(state.error.value, /Enter a hotel/)
})

test('changing account discards previous search and history including in-flight responses', async (context) => {
  const resolvers = []
  context.mock.method(globalThis, 'fetch', () => new Promise(resolve => resolvers.push(resolve)))
  const search = useSearch()
  search.hotelName.value = 'Valley'
  const pendingSearch = search.submitSearch()
  search.clear()
  const booking = useBookings()
  booking.userId.value = 'U001'
  const pendingHistory = booking.loadHistory()
  booking.userId.value = ''
  await booking.selectTraveler()
  resolvers[0](json([{ nightly_rate_cents: 12000 }]))
  resolvers[1](json([{ booking_id: 'old' }]))
  await Promise.all([pendingSearch, pendingHistory])
  assert.deepEqual(search.stays.value, [])
  assert.equal(search.hasSearched.value, false)
  assert.deepEqual(booking.bookings.value, [])
  assert.equal(booking.historyLoading.value, false)
})
