import assert from 'node:assert/strict'
import test from 'node:test'
import { lookupZip } from '../src/api/locations.js'
import { useZipLookup } from '../src/composables/useZipLookup.js'
import { useSearch } from '../src/composables/useSearch.js'

const json = (value, status = 200) => new Response(JSON.stringify(value), { status })
const location = { postcode: '16802', country_code: 'us', latitude: 40.8, longitude: -77.86 }

test('ZIP lookup waits for a click and uses the backend path with optional locality', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async (url) => {
    assert.equal(url, '/api/zip-location?postcode=16802')
    return json(location)
  })
  const state = useZipLookup()
  assert.equal(mock.mock.callCount(), 0)
  await state.lookup()
  assert.deepEqual(state.location.value, location)
  mock.mock.mockImplementation(async () => json({ ...location, locality: 'Fictional Locality' }))
  await state.lookup()
  assert.equal(state.location.value.locality, 'Fictional Locality')
})

test('new ZIP request clears old results and errors and blocks repeated clicks', async (context) => {
  let resolve
  const mock = context.mock.method(globalThis, 'fetch', () => new Promise(done => { resolve = done }))
  const state = useZipLookup()
  state.location.value = location
  state.error.value = 'Earlier failure'
  const pending = state.lookup()
  assert.equal(state.location.value, null)
  assert.equal(state.error.value, '')
  assert.equal(state.isLoading.value, true)
  await state.lookup()
  assert.equal(mock.mock.callCount(), 1)
  resolve(json(location))
  await pending
  assert.equal(state.isLoading.value, false)
  assert.deepEqual(state.location.value, location)
})

test('backend errors are displayed and a subsequent click can recover', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => json({}, 502))
  const state = useZipLookup()
  for (const [status, detail] of [
    [503, 'Geoapify key is not configured.'],
    [404, 'ZIP 16802 could not be resolved.'],
    [502, 'Location provider request failed.'],
  ]) {
    mock.mock.mockImplementation(async () => json({ detail }, status))
    await state.lookup()
    assert.equal(state.error.value, detail)
    assert.equal(state.location.value, null)
    assert.equal(state.isLoading.value, false)
  }
  mock.mock.mockImplementation(async () => json(location))
  await state.lookup()
  assert.equal(state.error.value, '')
  assert.deepEqual(state.location.value, location)
})

test('offline and malformed responses have clear fallback errors', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch', async () => { throw new Error('offline') })
  await assert.rejects(lookupZip('16802'), /Unable to reach the ZIP lookup service/)
  mock.mock.mockImplementation(async () => new Response('not JSON', { status: 502 }))
  await assert.rejects(lookupZip('16802'), /could not be completed/)
  for (const data of [null, {}, { ...location, latitude: null }, { ...location, longitude: 'invalid' }]) {
    mock.mock.mockImplementation(async () => json(data))
    await assert.rejects(lookupZip('16802'), /invalid response/)
  }
})

test('ZIP lookup does not change or block hotel-name search', async (context) => {
  let resolveZip
  context.mock.method(globalThis, 'fetch', async (url) => {
    if (url === '/api/zip-location?postcode=16802') return new Promise(done => { resolveZip = done })
    assert.equal(url, '/api/stays?hotel_name=Harbor')
    return json([{ hotel_name: 'Harbor Lantern Hotel' }])
  })
  const zip = useZipLookup()
  const search = useSearch()
  const pending = zip.lookup()
  search.hotelName.value = 'Harbor'
  await search.submitSearch()
  assert.equal(search.stays.value[0].hotel_name, 'Harbor Lantern Hotel')
  assert.equal(zip.isLoading.value, true)
  resolveZip(json(location))
  await pending
  assert.equal(search.hotelName.value, 'Harbor')
  assert.equal(search.stays.value.length, 1)
})

test('entered ZIP replaces the default and retains leading zeros', async (context) => {
  const requests = []
  context.mock.method(globalThis, 'fetch', async (url) => {
    requests.push(url)
    const postcode = new URL(url, 'http://localhost').searchParams.get('postcode')
    return json({ ...location, postcode })
  })
  const state = useZipLookup()
  for (const postcode of ['10001', '00501']) {
    state.postcode.value = ` ${postcode} `
    await state.lookup()
    assert.equal(state.postcode.value, postcode)
    assert.equal(state.location.value.postcode, postcode)
  }
  assert.deepEqual(requests, ['/api/zip-location?postcode=10001', '/api/zip-location?postcode=00501'])
})

test('invalid ZIP shows validation without making a request', async (context) => {
  const mock = context.mock.method(globalThis, 'fetch')
  const state = useZipLookup()
  for (const postcode of ['', '1680', '168020', 'abcde', '１６８０２']) {
    state.postcode.value = postcode
    await state.lookup()
    assert.equal(state.location.value, null)
    assert.equal(state.isLoading.value, false)
    assert.equal(state.error.value, 'Enter a five-digit U.S. ZIP code.')
    await assert.rejects(lookupZip(postcode), /five-digit/)
  }
  assert.equal(mock.mock.callCount(), 0)
})

test('editing the input clears the earlier ZIP result before another lookup', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => json(location))
  const state = useZipLookup()
  await state.lookup()
  assert.equal(state.location.value.postcode, '16802')
  state.postcode.value = '10001'
  assert.equal(state.location.value, null)
})

test('a result for a different ZIP is rejected', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => json(location))
  await assert.rejects(lookupZip('10001'), /invalid response/)
})
