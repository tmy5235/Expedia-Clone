import assert from 'node:assert/strict'
import test from 'node:test'
import { findHotels } from '../src/api/discovery.js'
import { useDiscovery } from '../src/composables/useDiscovery.js'

const json = (value, status = 200) => new Response(JSON.stringify(value), { status })
const hotel = { place_id: 'fictional-one', name: 'Fictional Hotel', address: null, latitude: 40.801, longitude: -73.041 }
const data = { provider: 'geoapify', center: { postcode: '00501', country_code: 'us', locality: null,
  latitude: 40.8, longitude: -73.04 }, radius_meters: 5000, result_limit: 20,
  limit_reached: false, omitted_count: 0, hotels: [hotel, { ...hotel, place_id: 'fictional-two', name: null }] }

test('discovery waits for submission, preserves leading zero and displays provider fields', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(url, '/api/discovery/hotels?postcode=00501')
    return json(data)
  })
  const state = useDiscovery()
  assert.equal(mock.mock.callCount(), 0)
  state.postcode.value = ' 00501 '
  await state.search()
  assert.equal(state.status.value, 'results')
  assert.deepEqual(state.result.value, data)
  assert.equal(state.postcode.value, '00501')
  assert.equal(state.selectedId.value, null)
})

test('list and map selections use one provider ID without additional requests', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json(data))
  const state = useDiscovery()
  state.postcode.value = '00501'
  await state.search()
  for (const id of ['fictional-one', 'fictional-two']) {
    state.select(id)
    assert.equal(state.selectedId.value, id)
    assert.equal(state.selectedHotel.value.place_id, id)
  }
  state.select('unknown')
  assert.equal(state.selectedId.value, 'fictional-two')
  assert.equal(mock.mock.callCount(), 1)
  state.postcode.value = '10001'
  assert.equal(state.result.value, null)
  assert.equal(state.selectedHotel.value, null)
  assert.equal(state.status.value, 'idle')
})

test('invalid input never calls the API', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch')
  const state = useDiscovery()
  for (const postcode of ['', '1234', '123456', '１２３４５', 'abcde']) {
    state.postcode.value = postcode
    await state.search()
    assert.equal(state.status.value, 'invalid')
    assert.match(state.error.value, /five-digit/)
    assert.equal(state.isLoading.value, false)
  }
  assert.equal(mock.mock.callCount(), 0)
})

test('empty, unresolved, rate limited and failed requests are distinct; retry recovers', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json({ ...data, hotels: [] }))
  const state = useDiscovery()
  state.postcode.value = '00501'
  await state.search()
  assert.equal(state.status.value, 'empty')
  assert.equal(state.error.value, '')
  for (const [code, expected] of [[404, 'unresolved'], [429, 'limited'], [502, 'failed'], [503, 'failed']]) {
    mock.mock.mockImplementation(async () => json({ detail: 'Safe provider feedback' }, code))
    await state.search()
    assert.equal(state.status.value, expected)
    assert.equal(state.error.value, 'Safe provider feedback')
    assert.equal(state.result.value, null)
    assert.equal(state.isLoading.value, false)
  }
  mock.mock.mockImplementation(async () => json(data))
  await state.search()
  assert.equal(state.status.value, 'results')
  assert.equal(state.error.value, '')
})

test('duplicate submissions are blocked and an edited ZIP discards a late response', async (context) => {
  let resolve
  const mock = context.mock.method(globalThis, 'fetch', () => new Promise(done => { resolve = done }))
  const state = useDiscovery()
  state.postcode.value = '00501'
  const pending = state.search()
  assert.equal(state.isLoading.value, true)
  await state.search()
  assert.equal(mock.mock.callCount(), 1)
  state.postcode.value = '10001'
  resolve(json(data))
  await pending
  assert.equal(state.result.value, null)
  assert.equal(state.isLoading.value, false)
})

test('malformed or mismatched successful responses and offline failure never become empty success', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json(null))
  for (const value of [null, {}, { ...data, center: { ...data.center, postcode: '10001' } },
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

test('a timed out request restores the search control and reports failure', async (context) => {
  context.mock.timers.enable({ apis: ['setTimeout'] })
  context.mock.method(globalThis, 'fetch', (_url, options) => new Promise((_resolve, reject) => {
    options.signal.addEventListener('abort', () => reject(new Error('aborted')))
  }))
  const state = useDiscovery()
  const pending = state.search()
  context.mock.timers.tick(30000)
  await pending
  assert.equal(state.isLoading.value, false)
  assert.equal(state.status.value, 'failed')
  assert.match(state.error.value, /timed out/)
})

test('replacing a selected result with invalid input clears both list and map selection', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json(data))
  const state = useDiscovery()
  state.postcode.value = '00501'
  await state.search()
  state.select('fictional-one')
  assert.equal(state.selectedHotel.value.name, 'Fictional Hotel')
  state.postcode.value = '123'
  await state.search()
  assert.equal(state.result.value, null)
  assert.equal(state.selectedId.value, null)
  assert.equal(state.selectedHotel.value, null)
  assert.equal(state.status.value, 'invalid')
  assert.equal(mock.mock.callCount(), 1)
})
