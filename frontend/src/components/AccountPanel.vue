<script setup>
import { ref } from 'vue'
defineProps({ user: { type: Object, default: null }, busy: Boolean, error: { type: String, default: '' }, message: { type: String, default: '' } })
const emit = defineEmits(['submit', 'logout', 'retry'])
const creating = ref(false)
const username = ref('')
const password = ref('')
function submit() {
  emit('submit', { username: username.value, password: password.value }, creating.value)
  password.value = ''
}
</script>
<template>
  <section aria-labelledby="account-heading" class="account-panel">
    <h2 id="account-heading">Your account</h2>
    <template v-if="user">
      <p>Signed in as <strong>{{ user.username }}</strong></p>
      <button :disabled="busy" @click="emit('logout')">Log out</button>
    </template>
    <template v-else>
      <p>Log in to book stays and view your booking history.</p>
      <form @submit.prevent="submit">
        <label for="username">Username</label>
        <input id="username" v-model="username" required minlength="3" maxlength="40" pattern="[A-Za-z0-9_]{3,40}" autocomplete="username" :disabled="busy" aria-describedby="username-help">
        <p id="username-help">3–40 letters, numbers, or underscores.</p>
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" required maxlength="100" :autocomplete="creating ? 'new-password' : 'current-password'" :disabled="busy">
        <div class="actions account-actions">
          <button type="submit" :disabled="busy">{{ creating ? 'Create account' : 'Log in' }}</button>
          <button type="button" :disabled="busy" @click="creating = !creating">{{ creating ? 'Back to login' : 'Create an account instead' }}</button>
        </div>
      </form>
      <p class="demo-note">Fictional classroom accounts only. Use a made-up password.</p>
    </template>
    <p v-if="busy" role="status">Updating account…</p>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <button v-if="error && !busy" @click="emit('retry')">Check current session</button>
    <p v-if="message" role="status">{{ message }}</p>
  </section>
</template>
<style scoped>
.account-panel { padding: 1.25rem; background: #f4f7fc; border: 1px solid #cdd9eb; border-radius: 0.5rem; margin: 1.5rem 0; }
h2 { margin-top: 0; }
form { margin-top: 1rem; max-width: 28rem; }
label { margin-top: 0.75rem; }
.account-actions { margin-top: 1rem; }
.demo-note, #username-help { font-size: 0.875rem; color: #4a5568; margin-top: 0.5rem; }
</style>
