import { ref, watch } from 'vue'
import { lookupZip } from '../api/locations.js'

export function useZipLookup() {
  const postcode = ref('16802')
  const submittedPostcode = ref('')
  const location = ref(null)
  const error = ref('')
  const isLoading = ref(false)

  watch(postcode, () => {
    location.value = null
    error.value = ''
  }, { flush: 'sync' })

  async function lookup() {
    if (isLoading.value) return
    location.value = null
    error.value = ''
    const query = postcode.value.trim()
    if (!/^[0-9]{5}$/.test(query)) {
      error.value = 'Enter a five-digit U.S. ZIP code.'
      return
    }
    postcode.value = query
    submittedPostcode.value = query
    isLoading.value = true
    try {
      location.value = await lookupZip(query)
    } catch (failure) {
      error.value = failure.message
    } finally {
      isLoading.value = false
    }
  }

  return { postcode, submittedPostcode, location, error, isLoading, lookup }
}
