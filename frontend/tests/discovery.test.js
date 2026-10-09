import assert from 'node:assert/strict'
import test from 'node:test'
import { findHotels } from '../src/api/discovery.js'
import { useDiscovery } from '../src/composables/useDiscovery.js'
import { findLocalFirstHotels, getLocalHotels, getSavedIds, saveLocalHotel, removeLocalHotel } from '../src/api/localHotels.js'

const json = (value, status = 200) => new Response(JSON.stringify(value), { status })
const hotel = { place_id: 'fictional-one', name: 'Fictional Hotel', address: null, latitude: 40.801, longitude: -73.041 }
const center = { postcode: '00501', country_code: 'us', locality: null, latitude: 40.8, longitude: -73.04 }
const data = { provider: 'geoapify', center, radius_meters: 5000, result_limit: 20,
  limit_reached: false, omitted_count: 0, hotels: [hotel, { ...hotel, place_id: 'fictional-two', name: null }] }
const nights = Array.from({ length: 5 }, (_, index) => ({ stay_date: `2026-10-${index + 10}`, nightly_rate_cents: 10000, rooms_available: 20 }))
const saved = { ...hotel, demo_nights: nights }
const local = { provider: 'geoapify', source: 'local', center, radius_meters: 5000, hotels: [saved] }
const empty = { ...local, center: null, hotels: [] }

function setup(context, options = {}) {
  const handlers = {
    local: () => json(empty), api: () => json(data), status: () => json({ saved_ids: [] }),
    save: () => json(saved), remove: () => new Response(null, { status: 204 }), ...options,
  }
  const calls = []
  context.mock.method(globalThis, 'fetch', (url, init = {}) => {
    calls.push({ url, ...init })
    if (url.startsWith('/api/discovery/')) return handlers.api(url, init)
    if (url.endsWith('/status')) return handlers.status(url, init)
    if (init.method === 'POST') return handlers.save(url, init)
    if (init.method === 'DELETE') return handlers.remove(url, init)
    return handlers.local(url, init)
  })
  const state = useDiscovery()
  state.postcode.value = '00501'
  return { state, calls, handlers }
}

test('local-first search preserves ZIP, stored context and server nightly values without API traffic', async context => {
  const stored = { ...local, hotels: [{ ...saved, demo_nights: [{ ...nights[0], nightly_rate_cents: 12345, rooms_available: 7 }] }] }
  const { state, calls } = setup(context, { local: () => json(stored) })
  assert.equal(calls.length, 0)
  state.postcode.value = ' 00501 '
  await state.search()
  assert.equal(state.source.value, 'local')
  assert.deepEqual(state.result.value, stored)
  assert.equal(state.postcode.value, '00501')
  assert.equal(state.savedIds.value.has(hotel.place_id), true)
  assert.equal(calls.length, 1)
  const refreshed = useDiscovery()
  refreshed.postcode.value = '00501'
  await refreshed.search()
  assert.equal(refreshed.savedIds.value.has(hotel.place_id), true)
})

test('successful empty local lookup precedes API and global provider-ID status lookup', async context => {
  const { state, calls } = setup(context, { status: () => json({ saved_ids: ['fictional-one'] }) })
  await state.search()
  assert.deepEqual(calls.map(c => c.url), ['/api/local-hotels?postcode=00501', '/api/discovery/hotels?postcode=00501', '/api/local-hotels/status'])
  assert.equal(state.source.value, 'api')
  assert.deepEqual(state.result.value, data)
  assert.equal(state.savedIds.value.has('fictional-one'), true)
  assert.equal(state.savedIds.value.has('fictional-two'), false)
})

test('failed, malformed and offline local lookups stop the search without falling back', async context => {
  const { state, calls, handlers } = setup(context)
  for (const handler of [() => json({ detail: 'Storage unavailable' }, 503), () => json({}),
    () => { throw new TypeError('offline') }]) {
    handlers.local = handler
    await state.search()
    assert.equal(state.status.value, 'failed')
    assert.equal(state.result.value, null)
    assert.ok(state.error.value)
  }
  assert.ok(calls.every(call => call.url.startsWith('/api/local-hotels?')))
})

test('status failure never labels API hotels as unsaved', async context => {
  const { state } = setup(context, { status: () => json({ detail: 'Status unavailable' }, 503) })
  await state.search()
  assert.equal(state.status.value, 'failed')
  assert.equal(state.result.value, null)
})

test('list and map selections use one provider ID without additional requests', async context => {
  const { state, calls } = setup(context)
  await state.search()
  for (const id of ['fictional-one', 'fictional-two']) {
    state.select(id)
    assert.equal(state.selectedId.value, id)
    assert.equal(state.selectedHotel.value.place_id, id)
  }
  state.select('unknown')
  assert.equal(state.selectedId.value, 'fictional-two')
  assert.equal(calls.length, 3)
  state.postcode.value = '10001'
  assert.equal(state.result.value, null)
  assert.equal(state.selectedHotel.value, null)
  assert.equal(state.status.value, 'idle')
})

test('invalid input never requests local storage or API and clears stale selection', async context => {
  const { state, calls } = setup(context)
  await state.search()
  state.select('fictional-one')
  const count = calls.length
  for (const postcode of ['', '1234', '123456', '１２３４５', 'abcde']) {
    state.postcode.value = postcode
    await state.search()
    assert.equal(state.status.value, 'invalid')
    assert.match(state.error.value, /five-digit/)
    assert.equal(state.result.value, null)
    assert.equal(state.selectedId.value, null)
  }
  assert.equal(calls.length, count)
})

test('API empty, unresolved, rate-limited and failed responses remain distinct; retry recovers', async context => {
  const { state, handlers } = setup(context, { api: () => json({ ...data, hotels: [] }) })
  await state.search()
  assert.equal(state.status.value, 'empty')
  for (const [code, expected] of [[404, 'unresolved'], [429, 'limited'], [502, 'failed'], [503, 'failed']]) {
    handlers.api = () => json({ detail: 'Safe provider feedback' }, code)
    await state.search()
    assert.equal(state.status.value, expected)
    assert.equal(state.error.value, 'Safe provider feedback')
    assert.equal(state.result.value, null)
  }
  handlers.api = () => json(data)
  await state.search()
  assert.equal(state.status.value, 'results')
})

test('duplicate submissions are blocked and changed ZIP discards a late local response', async context => {
  let resolve
  const { state, calls } = setup(context, { local: () => new Promise(done => { resolve = done }) })
  const pending = state.search()
  await state.search()
  assert.equal(calls.length, 1)
  state.postcode.value = '10001'
  resolve(json(local))
  await pending
  assert.equal(state.result.value, null)
  assert.equal(state.isLoading.value, false)
  assert.equal(calls.length, 1)
})

test('a timed out local request restores controls without falling back', async context => {
  context.mock.timers.enable({ apis: ['setTimeout'] })
  const { state, calls } = setup(context, { local: (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('aborted')))
  }) })
  const pending = state.search()
  context.mock.timers.tick(30000)
  await pending
  assert.equal(state.isLoading.value, false)
  assert.equal(state.status.value, 'failed')
  assert.match(state.error.value, /timed out/)
  assert.equal(calls.length, 1)
})

test('save uses current result context, blocks duplicate requests and marks saved only after success', async context => {
  let resolve
  const { state, calls } = setup(context, { save: () => new Promise(done => { resolve = done }) })
  await state.search()
  state.select(hotel.place_id)
  const pending = state.addLocal(hotel)
  await state.addLocal(hotel)
  assert.equal(state.pendingIds.value.has(hotel.place_id), true)
  assert.equal(state.savedIds.value.has(hotel.place_id), false)
  assert.equal(state.hasPending.value, true)
  const count = calls.length
  await state.search()
  assert.equal(calls.length, count)
  assert.deepEqual(JSON.parse(calls.at(-1).body), { hotel, center })
  resolve(json(saved))
  await pending
  assert.equal(state.savedIds.value.has(hotel.place_id), true)
  assert.equal(state.pendingIds.value.size, 0)
  assert.equal(state.selectedId.value, hotel.place_id)
  assert.equal(state.actionFeedback.value[hotel.place_id].text, 'Saved locally. Ready to compare stays.')
  await state.addLocal(hotel)
  assert.equal(calls.length, count)
})

test('failed saves and removals preserve UI state and allow retries', async context => {
  const { state, handlers, calls } = setup(context, { save: () => json({ detail: 'Save failed' }, 503) })
  await state.search()
  await state.removeLocal(hotel)
  assert.equal(calls.length, 3)
  await state.addLocal(hotel)
  assert.equal(state.savedIds.value.has(hotel.place_id), false)
  assert.equal(state.actionFeedback.value[hotel.place_id].failed, true)
  handlers.save = () => json(saved)
  await state.addLocal(hotel)
  handlers.remove = () => json({ detail: 'Remove failed' }, 503)
  await state.removeLocal(hotel)
  assert.equal(state.savedIds.value.has(hotel.place_id), true)
  assert.equal(state.actionFeedback.value[hotel.place_id].text, 'Remove failed')
  handlers.remove = () => new Response(null, { status: 204 })
  await state.removeLocal(hotel)
  assert.equal(state.savedIds.value.has(hotel.place_id), false)
  assert.equal(state.result.value.hotels.length, 2) // API card stays available to add again.
})

test('local removal updates results/map membership only after success; last removal never auto-fetches API', async context => {
  let resolve
  const { state, calls } = setup(context, { local: () => json(local), remove: () => new Promise(done => { resolve = done }) })
  await state.search()
  state.select(hotel.place_id)
  const pending = state.removeLocal(saved)
  assert.equal(state.result.value.hotels.length, 1)
  assert.equal(state.savedIds.value.has(hotel.place_id), true)
  resolve(new Response(null, { status: 204 }))
  await pending
  assert.equal(state.result.value.hotels.length, 0)
  assert.equal(state.selectedId.value, null)
  assert.equal(state.status.value, 'empty')
  assert.equal(state.source.value, 'local')
  assert.equal(calls.length, 2)
  assert.match(state.actionFeedback.value[hotel.place_id].text, /Removed/)
})

test('late mutation result cannot alter a different search context', async context => {
  let resolve
  const { state } = setup(context, { save: () => new Promise(done => { resolve = done }) })
  await state.search()
  const pending = state.addLocal(hotel)
  state.postcode.value = '10001'
  resolve(json(saved))
  await pending
  assert.equal(state.result.value, null)
  assert.equal(state.savedIds.value.size, 0)
  assert.deepEqual(state.actionFeedback.value, {})
})

test('Part 1 malformed responses and offline errors retain original validation', async context => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json(null))
  for (const value of [null, {}, { ...data, center: { ...center, postcode: '10001' } },
    { ...data, hotels: [{ ...hotel, latitude: 100 }] }, { ...data, hotels: [hotel, hotel] },
    { ...data, hotels: [{ ...hotel, name: {} }] }, { ...data, radius_meters: 10000 }]) {
    mock.mock.mockImplementation(async () => json(value))
    await assert.rejects(findHotels('00501'), /invalid response/)
  }
  mock.mock.mockImplementation(async () => { throw new TypeError('offline') })
  await assert.rejects(findHotels('00501'), /Unable to reach/)
  mock.mock.mockImplementation(async () => new Response('<html>proxy error</html>', { status: 502 }))
  await assert.rejects(findHotels('00501'), /search failed/)
})

test('malformed local records, status and mutation receipts are rejected', async context => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json(null))
  for (const value of [null, {}, { ...local, center: { ...center, postcode: '10001' } },
    { ...local, hotels: [saved, saved] }, { ...local, hotels: [{ ...saved, latitude: 100 }] },
    { ...local, hotels: [{ ...saved, demo_nights: [{ ...nights[0], rooms_available: -1 }] }] }]) {
    mock.mock.mockImplementation(async () => json(value))
    await assert.rejects(getLocalHotels('00501'), /invalid response/)
  }
  mock.mock.mockImplementation(async () => json({ saved_ids: ['unrequested'] }))
  await assert.rejects(getSavedIds([hotel.place_id]), /invalid response/)
  mock.mock.mockImplementation(async () => json({ ...saved, place_id: 'wrong-id' }))
  await assert.rejects(saveLocalHotel(hotel, center), /invalid response/)
  mock.mock.mockImplementation(async () => json({ ok: false }))
  await assert.rejects(removeLocalHotel(hotel.place_id), /invalid response/)
  mock.mock.mockImplementation(async () => json(empty))
  const controller = new AbortController()
  controller.abort()
  await assert.rejects(findLocalFirstHotels('00501', controller.signal), /cancelled/)
})
