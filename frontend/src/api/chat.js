export class ChatError extends Error {
  constructor(message, conversationId = null) {
    super(message)
    this.conversationId = conversationId
  }
}

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`/api/chat${path}`, { cache: 'no-store', signal: AbortSignal.timeout(100000), ...options })
  } catch {
    throw new ChatError('Unable to reach the assistant, or the request timed out. Reload saved conversations before retrying.')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new ChatError(typeof data?.detail === 'string' ? data.detail : 'The assistant request failed. Please try again.', data?.conversation_id)
  if (data === null) throw new ChatError('The assistant returned an invalid response.')
  return data
}

export const getChatCatalog = () => request('/catalog')
export const getChatStatus = () => request('/status')
export const listConversations = () => request('/conversations')
export const getConversation = id => request(`/conversations/${encodeURIComponent(id)}`)
export async function askHotelQuestion(question, conversationId) {
  const data = await request('', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_id: conversationId }) })
  if (typeof data.answer !== 'string' || typeof data.conversation_id !== 'string' || !Array.isArray(data.records)) {
    throw new ChatError('The assistant returned an invalid response.')
  }
  return data
}
