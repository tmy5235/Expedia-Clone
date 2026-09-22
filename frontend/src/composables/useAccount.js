import { ref } from 'vue'
import * as api from '../api/accounts.js'

export function useAccount() {
  const user = ref(null)
  const busy = ref(false)
  const error = ref('')
  const message = ref('')
  async function run(action) {
    if (busy.value) return
    busy.value = true
    error.value = ''
    message.value = ''
    try { await action() } catch (failure) { error.value = failure.message }
    finally { busy.value = false }
  }
  return {
    user, busy, error, message,
    initialize: () => run(async () => { user.value = await api.getSession() }),
    submit: (credentials, creating) => run(async () => {
      if (creating) {
        await api.createAccount(credentials)
        message.value = 'Account created. Log in with your new username and password.'
      } else {
        user.value = null
        user.value = await api.login(credentials)
        message.value = 'Logged in successfully.'
      }
    }),
    logout: () => run(async () => {
      await api.logout()
      user.value = null
      message.value = 'You are logged out.'
    }),
  }
}
