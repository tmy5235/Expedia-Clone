import assert from 'node:assert/strict'
import test from 'node:test'
import { setImmediate } from 'node:timers'
import { askHotelQuestion } from '../src/api/chat.js'
import { useChat } from '../src/composables/useChat.js'

const json = (body, status = 200) => new Response(JSON.stringify(body), { status })
const id = '00000000-0000-0000-0000-000000000001'
const messages = [{ message_id: 1, turn_id: 'turn', stage: 'question', content: 'Test question', role: 'user' },
  { message_id: 2, turn_id: 'turn', stage: 'answer', content: 'Simulated answer', role: 'assistant' }]
function setup(context) {
  const calls = []
  const handlers = { ask: () => json({ answer: 'Simulated answer', conversation_id: id, records: [] }) }
  context.mock.method(globalThis, 'fetch', async (url, options = {}) => {
    calls.push({ url, ...options })
    if (url.endsWith('/catalog')) return json({ hotel_count: 1, zips: [{ postcode: '00501', hotel_count: 1, nights: ['2026-10-11','2026-10-12'] }] })
    if (url.endsWith('/status')) return json({ configured: true, model: 'fixture', mode: 'MOCK' })
    if (url.endsWith('/conversations')) return json([{ conversation_id: id, title: 'Test question' }])
    if (url.includes('/conversations/')) return json({ conversation_id: id, messages })
    return handlers.ask(url, options)
  })
  return { state: useChat(), calls, handlers }
}

test('refresh loads durable conversation and new conversation clears displayed history', async context => {
  const { state } = setup(context)
  await state.refresh()
  assert.equal(state.conversationId.value, id)
  assert.deepEqual(state.messages.value, messages)
  assert.equal(state.status.value.model, 'fixture')
  state.newConversation()
  assert.equal(state.conversationId.value, null)
  assert.deepEqual(state.messages.value, [])
  await state.select(id)
  assert.deepEqual(state.messages.value, messages)
})

test('send validates input, posts only to backend and loads persisted trace', async context => {
  const { state, calls } = setup(context)
  state.question.value = '  '
  await state.send()
  assert.equal(calls.length, 0)
  assert.match(state.error.value, /Enter a hotel question/)
  state.question.value = '  What is cheapest?  '
  await state.send()
  assert.deepEqual(JSON.parse(calls.find(call => call.method === 'POST').body), { question: 'What is cheapest?', conversation_id: null })
  assert.equal(calls.find(call => call.method === 'POST').url, '/api/chat')
  assert.equal(state.conversationId.value, id)
  assert.equal(state.question.value, '')
  assert.deepEqual(state.messages.value, messages)
})

test('pending request prevents duplicate send and conversation switch', async context => {
  const { state, handlers, calls } = setup(context)
  let finish
  handlers.ask = () => new Promise(resolve => { finish = resolve })
  state.question.value = 'Test'
  const pending = state.send()
  await new Promise(resolve => setImmediate(resolve))
  await state.send()
  await state.select(id)
  state.newConversation()
  assert.equal(calls.filter(call => call.method === 'POST').length, 1)
  assert.equal(state.busy.value, true)
  finish(json({ answer: 'done', conversation_id: id, records: [] }))
  await pending
  assert.equal(state.busy.value, false)
})

test('failed question retains input and loads saved failure trace for retry', async context => {
  const { state, handlers } = setup(context)
  handlers.ask = () => json({ detail: 'Model rate limit', conversation_id: id }, 429)
  state.question.value = 'Retry this'
  await state.send()
  assert.equal(state.question.value, 'Retry this')
  assert.equal(state.conversationId.value, id)
  assert.equal(state.error.value, 'Model rate limit')
  assert.equal(state.busy.value, false)
  handlers.ask = () => json({ answer: 'done', conversation_id: id, records: [] })
  await state.send()
  assert.equal(state.error.value, '')
})

test('offline and malformed replies show safe errors', async context => {
  const mock = context.mock.method(globalThis, 'fetch', async () => { throw new Error('offline') })
  await assert.rejects(askHotelQuestion('test', null), /Unable to reach/)
  mock.mock.mockImplementation(async () => json({}))
  await assert.rejects(askHotelQuestion('test', null), /invalid response/)
  mock.mock.mockImplementation(async () => new Response('broken', { status: 502 }))
  await assert.rejects(askHotelQuestion('test', null), /request failed/)
})

test('saved collection is loaded from the server and can be refreshed independently', async context => {
  const { state } = setup(context)
  await state.refreshCatalog()
  assert.equal(state.catalog.value.hotel_count, 1)
  assert.equal(state.catalog.value.zips[0].postcode, '00501')
  assert.equal(state.conversationId.value, null)
})
