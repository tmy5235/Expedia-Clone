<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useChat } from '../composables/useChat.js'
import { answerBlocks, readableError, suggestedQuestions } from '../utils/chatPresentation.js'

const props = defineProps({ collectionKey: { type: String, default: '' } })
const { question, conversations, conversationId, messages, busy, error, status, catalog, catalogError,
  refreshCatalog, refresh, select, newConversation, send } = useChat()
const composer = ref(null)
const messageList = ref(null)
const examples = computed(() => suggestedQuestions(catalog.value))
const turns = computed(() => {
  const grouped = new Map()
  for (const message of messages.value) {
    if (!grouped.has(message.turn_id)) grouped.set(message.turn_id, { id: message.turn_id, steps: [] })
    const turn = grouped.get(message.turn_id)
    if (['question', 'answer', 'error'].includes(message.stage)) turn[message.stage] = message.content
    turn.steps.push(message)
  }
  return [...grouped.values()]
})
const pretty = content => {
  try { return JSON.stringify(JSON.parse(content), null, 2) } catch { return content }
}
async function useExample(text) {
  question.value = text
  await nextTick()
  composer.value?.focus()
}
async function submit() {
  await send()
  await nextTick()
  if (messageList.value) messageList.value.scrollTop = messageList.value.scrollHeight
  composer.value?.focus()
}
watch(() => props.collectionKey, refreshCatalog)
onMounted(refresh)
</script>

<template>
  <section id="hotel-assistant" class="assistant" aria-labelledby="assistant-title">
    <div class="assistant-heading">
      <div><p class="eyebrow">YOUR SAVED COLLECTION</p><h2 id="assistant-title">Compare saved hotels</h2></div>
    </div>
    <p class="intro">Find a stay that fits your dates and budget. The assistant uses hotels you’ve added to your local collection.</p>

    <div v-if="catalog?.hotel_count === 0" class="getting-started" role="status">
      <div><h3>Save a few hotels to get started</h3><p>Your collection is empty. The chatbot needs saved hotels before it can compare stays.</p></div>
      <ol><li>Search for a ZIP above.</li><li>Choose <strong>Add to Local</strong> on hotels you like.</li><li>Come back here and choose a suggested question.</li></ol>
      <a class="search-link" href="#hotel-search">Find hotels to save <span aria-hidden="true">↑</span></a>
    </div>
    <div v-else-if="catalog" class="collection-summary">
      <p><strong>{{ catalog.hotel_count }} {{ catalog.hotel_count === 1 ? 'hotel' : 'hotels' }} saved</strong><span> · Your collection only, not every hotel in the area</span></p>
      <p v-for="zip in catalog.zips" :key="zip.postcode" class="date-summary"><strong>ZIP {{ zip.postcode }}</strong> · {{ zip.hotel_count }} {{ zip.hotel_count === 1 ? 'hotel' : 'hotels' }} · Recorded nights: {{ zip.nights.join(', ') || 'No nightly data saved' }}</p>
    </div>
    <p v-if="catalogError" class="chat-error" role="alert">{{ catalogError }}</p>
    <p v-if="status && !status.configured" class="chat-error" role="status">The assistant is currently unavailable. Please try again later.</p>

    <div class="chat-layout">
      <aside aria-label="Saved conversations">
        <div class="history-heading"><h3>Conversations</h3><button type="button" class="reload" :disabled="busy" @click="refresh">Reload</button></div>
        <button type="button" class="new-chat" :disabled="busy" @click="newConversation">+ New conversation</button>
        <ol class="conversation-list">
          <li v-for="conversation in conversations" :key="conversation.conversation_id">
            <button type="button" :disabled="busy" :aria-pressed="conversationId === conversation.conversation_id" :title="conversation.title" @click="select(conversation.conversation_id)"><span>{{ conversation.title }}</span></button>
          </li>
        </ol>
        <p v-if="!conversations.length" class="history-note">Your conversations will appear here.</p>
        <p class="history-note">Your conversations are saved on this computer.</p>
      </aside>
      <div class="chat-main">
        <div ref="messageList" class="messages" aria-label="Conversation" :aria-busy="busy">
          <div v-if="!turns.length" class="chat-empty">
            <h3>{{ catalog?.hotel_count ? 'What matters most for your stay?' : 'Your next comparison starts here.' }}</h3>
            <p>{{ catalog?.hotel_count ? 'Ask for the cheapest option, set a budget, or compare a complete stay.' : 'Once you save hotels, suggested questions will use their actual ZIP and recorded dates.' }}</p>
          </div>
          <article v-for="turn in turns" :key="turn.id" class="turn">
            <div class="user-message"><p class="speaker">You</p><p class="message">{{ turn.question }}</p></div>
            <div v-if="turn.answer" class="answer">
              <p class="speaker">Hotel assistant</p>
              <template v-for="(block, index) in answerBlocks(turn.answer)" :key="index">
                <ol v-if="block.kind === 'list'" class="answer-list"><li v-for="(item, itemIndex) in block.items" :key="itemIndex">{{ item }}</li></ol>
                <p v-else class="message">{{ block.text }}</p>
              </template>
            </div>
            <p v-if="turn.error" class="chat-error">{{ readableError(turn.error) }}</p>
            <details class="trace">
              <summary>View supporting records &amp; SQL</summary>
              <p class="trace-id">Conversation: {{ conversationId }}</p>
              <div v-for="step in turn.steps" :key="step.message_id" class="trace-step">
                <details v-if="['instructions', 'query_request', 'answer_request'].includes(step.stage)">
                  <summary>{{ step.stage }} · {{ step.role }}</summary><pre>{{ pretty(step.content) }}</pre>
                </details>
                <template v-else><h4>{{ step.stage }} · {{ step.role }}</h4><pre>{{ pretty(step.content) }}</pre></template>
                <small>{{ step.timestamp }} · prompt {{ step.prompt_version }}</small>
              </div>
            </details>
          </article>
        </div>
        <div v-if="examples.length" class="suggestions">
          <p class="suggestions-label">TRY A QUESTION <span>Using your saved ZIP and dates</span></p>
          <div class="example-buttons"><button v-for="example in examples" :key="example.label" type="button" :disabled="busy" :title="example.text" @click="useExample(example.text)">{{ example.label }} <span aria-hidden="true">↗</span></button></div>
        </div>
        <form @submit.prevent="submit">
          <label for="hotel-question">Your question</label>
          <textarea id="hotel-question" ref="composer" v-model="question" rows="3" maxlength="2000" :disabled="busy" aria-describedby="question-help" placeholder="Include a saved ZIP, a stay date and what you’d like to compare…" />
          <div class="composer-footer"><p id="question-help">Use exact dates and a year. Checkout is not a charged night.</p><button class="send" type="submit" :disabled="busy || status?.configured === false">{{ busy ? 'Working…' : 'Send question' }}</button></div>
        </form>
        <p v-if="busy" class="pending" role="status">Checking your saved collection…</p>
        <p v-if="error && !turns.some(turn => turn.error === error)" class="chat-error" role="alert">{{ readableError(error) }}</p>
      </div>
    </div>
    <div class="assistant-footer"><p>Rates and availability are simulated. Booking is not available.</p></div>
  </section>
</template>

<style scoped>
.assistant { margin: 3rem 0; padding: 2rem; background: #fff; border: 1px solid #d8e3dd; border-radius: 18px; scroll-margin-top: 1rem; color: #193f45; font-size: .9375rem; line-height: 1.6; }
.assistant p, .assistant h3, .assistant h4 { margin: 0; }
.assistant-heading { display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
h2 { font-size: clamp(1.5rem, 3vw, 2rem); margin: .3rem 0; letter-spacing: -.025em; font-weight: 650; line-height: 1.25; }
.assistant h3 { font-size: 1rem; font-weight: 650; line-height: 1.4; }
.eyebrow { font-size: .68rem; font-weight: 700; letter-spacing: .12em; color: #54766b; }
.assistant .intro { margin: .75rem 0 1.4rem; line-height: 1.65; max-width: 66ch; color: #536966; }
.getting-started, .collection-summary { background: #f3f7f3; border: 1px solid #e0e9df; border-radius: 12px; padding: 1.1rem 1.25rem; margin-bottom: 1.75rem; }
.getting-started p { color: #526963; max-width: 68ch; margin-top: .35rem; font-size: .85rem; }
.getting-started ol { padding-left: 1.3rem; margin: .85rem 0; font-size: .85rem; }
.getting-started li { padding: .15rem 0 .15rem .2rem; }
.search-link { color: #215b60; font-weight: 650; font-size: .85rem; text-underline-offset: 3px; }
.collection-summary { font-size: .85rem; }
.collection-summary span { color: #637770; }
.assistant .date-summary { margin-top: .35rem; font-size: .75rem; color: #526963; overflow-wrap: anywhere; }
.history-note, small, #question-help, .trace-id { color: #60756e; font-size: .72rem; overflow-wrap: anywhere; }
.chat-layout { display: grid; grid-template-columns: 205px minmax(0, 1fr); gap: 1.75rem; }
aside { border-right: 1px solid #e0e8e3; padding-right: 1.25rem; min-width: 0; }
.history-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: .75rem; }
.history-heading h3 { font-size: .8rem; }
button { font: inherit; font-size: .8rem; line-height: 1.45; color: #194b47; background: #f5f8f5; border: 1px solid #c1d1c7; border-radius: 8px; padding: .65rem .8rem; cursor: pointer; text-align: left; }
button:hover { background: #e7f0e9; }
button:focus-visible, textarea:focus-visible, summary:focus-visible, a:focus-visible { outline: 3px solid #277c86; outline-offset: 3px; }
button:disabled { opacity: .6; cursor: wait; }
.reload { border: 0; background: transparent; font-size: .72rem; padding: .3rem; }
.new-chat { width: 100%; text-align: center; }
button[aria-pressed="true"] { background: #e6efe7; border-color: #76a38d; }
.conversation-list { padding: 0; list-style: none; max-height: 24rem; overflow: auto; margin: .8rem 0; display: grid; gap: .5rem; }
.conversation-list button { width: 100%; background: white; border-color: #e0e8e3; }
.conversation-list button[aria-pressed="true"] { background: #e6efe7; border-color: #76a38d; }
.conversation-list span { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; overflow-wrap: anywhere; }
.assistant .history-note { margin-top: .8rem; line-height: 1.6; }
.chat-main { min-width: 0; }
.messages { max-height: 34rem; overflow: auto; padding: .1rem .7rem .1rem .1rem; scrollbar-gutter: stable; }
.chat-empty { padding: 1.25rem 0; line-height: 1.65; max-width: 58ch; }
.chat-empty p { color: #64786f; margin-top: .5rem; font-size: .85rem; }
.assistant .speaker { font-size: .68rem; font-weight: 700; letter-spacing: .055em; text-transform: uppercase; margin-bottom: .45rem; color: #5e786d; }
.message { white-space: pre-wrap; overflow-wrap: anywhere; line-height: 1.7; max-width: 68ch; }
.user-message { padding: .9rem 1rem; border-radius: 10px; background: #f0f5f0; margin-bottom: 1.2rem; }
.user-message .message { font-size: .88rem; }
.answer { font-size: .9rem; }
.answer .message + .message, .answer-list + .message { margin-top: .9rem; }
.answer-list { padding-left: 1.25rem; margin: .8rem 0; display: grid; gap: .9rem; max-width: 68ch; }
.answer-list li { line-height: 1.7; padding-left: .25rem; overflow-wrap: anywhere; }
.turn { padding-bottom: 1.2rem; margin-bottom: 1.5rem; border-bottom: 1px solid #e6ece7; }
.turn:last-child { margin-bottom: .5rem; }
.trace { margin-top: 1rem; font-size: .72rem; color: #60766b; }
summary { cursor: pointer; padding: .3rem 0; }
.trace-step { margin: 1rem 0; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; max-height: 22rem; overflow: auto; background: #f2f5f4; padding: .75rem; font-size: .7rem; color: #193f45; }
.suggestions { padding-top: 1.1rem; }
.suggestions-label { font-size: .65rem; font-weight: 700; letter-spacing: .06em; }
.suggestions-label span { font-weight: 400; letter-spacing: normal; color: #64786f; margin-left: .5rem; }
.example-buttons { display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .55rem; }
.example-buttons button { font-size: .73rem; padding: .55rem .7rem; background: white; }
.example-buttons span { padding-left: .35rem; }
form { margin-top: 1.2rem; }
label { display: block; font-size: .8rem; font-weight: 650; margin-bottom: .5rem; }
textarea { width: 100%; box-sizing: border-box; resize: vertical; border: 1px solid #a7bfb1; border-radius: 10px; padding: .85rem; font: inherit; font-size: .88rem; line-height: 1.55; color: #193f45; background: white; }
textarea::placeholder { color: #819088; }
.composer-footer { display: flex; justify-content: space-between; align-items: center; gap: 1rem; margin: .65rem 0; }
.send { background: #215b60; color: white; flex-shrink: 0; text-align: center; }
.send:hover { background: #17474b; }
.assistant .chat-error { background: #fff4ee; color: #842d20; padding: .85rem; border-radius: 8px; margin: .8rem 0; font-size: .85rem; overflow-wrap: anywhere; }
.pending { font-size: .8rem; color: #597267; }
.assistant-footer { border-top: 1px solid #e6ece7; margin-top: 1.5rem; padding-top: 1rem; display: flex; justify-content: space-between; gap: 1rem; color: #6a7e74; font-size: .7rem; }
@media(max-width: 48rem) { .assistant { padding: 1.25rem; } .chat-layout { grid-template-columns: 1fr; gap: 1rem; } aside { border-right: 0; border-bottom: 1px solid #e0e8e3; padding: 0 0 1rem; } .conversation-list { max-height: 8rem; } .assistant-heading { align-items: start; flex-direction: column; gap: .6rem; } .assistant-footer { flex-direction: column; gap: .3rem; } }
@media(max-width: 30rem) { .composer-footer { align-items: start; flex-direction: column; } .send { width: 100%; } .suggestions-label span { display: block; margin-left: 0; } }
</style>
