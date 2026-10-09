import { ref } from 'vue'
import { askHotelQuestion, getChatStatus, getChatCatalog, getConversation, listConversations } from '../api/chat.js'

export function useChat() {
  const question = ref('')
  const conversations = ref([])
  const conversationId = ref(null)
  const messages = ref([])
  const busy = ref(false)
  const error = ref('')
  const status = ref(null)
  const catalog = ref(null)
  const catalogError = ref('')

  async function refreshCatalog() {
    try {
      catalog.value = await getChatCatalog()
      catalogError.value = ''
    } catch {
      catalog.value = null
      catalogError.value = 'Saved hotel details could not be loaded. Select Reload conversations to try again.'
    }
  }

  async function refresh() {
    if (busy.value) return
    busy.value = true
    error.value = ''
    try {
      status.value = await getChatStatus()
      await refreshCatalog()
      conversations.value = await listConversations()
      const id = conversationId.value || conversations.value[0]?.conversation_id
      if (id) {
        const data = await getConversation(id)
        conversationId.value = id
        messages.value = data.messages
      }
    } catch (failure) { error.value = failure.message }
    finally { busy.value = false }
  }

  async function select(id) {
    if (busy.value) return
    busy.value = true
    error.value = ''
    try {
      const data = await getConversation(id)
      conversationId.value = id
      messages.value = data.messages
    } catch (failure) { error.value = failure.message }
    finally { busy.value = false }
  }

  function newConversation() {
    if (busy.value) return
    conversationId.value = null
    messages.value = []
    error.value = ''
    question.value = ''
  }

  async function send() {
    if (busy.value) return
    const text = question.value.trim()
    if (!text || text.length > 2000) {
      error.value = 'Enter a hotel question of 1–2,000 characters.'
      return
    }
    busy.value = true
    error.value = ''
    try {
      await refreshCatalog()
      const reply = await askHotelQuestion(text, conversationId.value)
      conversationId.value = reply.conversation_id
      question.value = ''
    } catch (failure) {
      error.value = failure.message
      if (failure.conversationId) conversationId.value = failure.conversationId
    }
    try {
      if (conversationId.value) messages.value = (await getConversation(conversationId.value)).messages
      conversations.value = await listConversations()
    } catch {
      error.value += ' Saved history could not be loaded. Use Reload conversations.'
    } finally { busy.value = false }
  }
  return { question, conversations, conversationId, messages, busy, error, status, catalog, catalogError, refreshCatalog, refresh, select, newConversation, send }
}
