import assert from 'node:assert/strict'
import test from 'node:test'
import { answerBlocks, suggestedQuestions, readableError } from '../src/utils/chatPresentation.js'

test('examples use actual saved ZIP and recorded dates, preserving leading zeros', () => {
  const examples = suggestedQuestions({ zips: [{ postcode:'00501', nights:['2026-11-02','2026-11-03'] }] })
  assert.equal(examples.length, 3)
  assert.ok(examples.every(e => e.text.includes('00501') && e.text.includes('Nov 2, 2026')))
  assert.match(examples[2].text, /checking out Nov 4, 2026/)
  assert.deepEqual(suggestedQuestions({zips:[]}), [])
  assert.equal(suggestedQuestions({zips:[{postcode:'16803',nights:['2026-10-11','2026-10-13']}]}).length, 2)
})

test('long plain text answers become paragraphs and lists without injecting markup', () => {
  const blocks = answerBlocks('Two choices.\n\n1. Hotel A: $100\n\n2. Hotel B: $120\n\n<script>alert(1)</script>')
  assert.deepEqual(blocks, [{kind:'paragraph',text:'Two choices.'},
    {kind:'list',items:['Hotel A: $100','Hotel B: $120']},
    {kind:'paragraph',text:'<script>alert(1)</script>'}])
  assert.match(readableError('The query must return hotel_id and total_cents only.'), /suggested question/)
  assert.equal(readableError('Model rate limit'), 'Model rate limit')
})
