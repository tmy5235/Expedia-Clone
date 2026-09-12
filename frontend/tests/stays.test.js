import assert from 'node:assert/strict'
import test from 'node:test'

import { searchStays } from '../src/api/stays.js'


test('requests stays using a trimmed and encoded hotel name', async (context) => {
  const requestedUrls = []
  context.mock.method(globalThis, 'fetch', async (url) => {
    requestedUrls.push(url)
    return new Response(JSON.stringify([{ trip_id: 'T001' }]), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    })
  })

  const stays = await searchStays('  Harbor Lantern Hotel  ')

  assert.deepEqual(requestedUrls, ['/api/stays?hotel_name=Harbor+Lantern+Hotel'])
  assert.deepEqual(stays, [{ trip_id: 'T001' }])
})


test('rejects a blank hotel name without sending a request', async (context) => {
  const fetchMock = context.mock.method(globalThis, 'fetch')

  await assert.rejects(searchStays('   '), /Enter a hotel name/)
  assert.equal(fetchMock.mock.callCount(), 0)
})


test('uses the API error message when a search fails', async (context) => {
  context.mock.method(
    globalThis,
    'fetch',
    async () =>
      new Response(JSON.stringify({ detail: 'Unable to read hotels.csv.' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }),
  )

  await assert.rejects(searchStays('Harbor'), /Unable to read hotels.csv/)
})


test('reports a connection failure clearly', async (context) => {
  context.mock.method(globalThis, 'fetch', async () => {
    throw new TypeError('network failed')
  })

  await assert.rejects(searchStays('Harbor'), /Unable to reach the hotel search service/)
})
