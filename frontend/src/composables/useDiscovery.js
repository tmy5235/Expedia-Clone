import { computed, ref, watch } from 'vue'
import { findHotels } from '../api/discovery.js'

export function useDiscovery() {
  const postcode = ref('16802')
  const result = ref(null)
  const selectedId = ref(null)
  const status = ref('idle')
  const error = ref('')
  const isLoading = computed(() => status.value === 'loading')
  const selectedHotel = computed(() => result.value?.hotels.find(hotel => hotel.place_id === selectedId.value) || null)
  let requestId = 0
  let controller

  function clear() {
    requestId++
    controller?.abort()
    result.value = null
    selectedId.value = null
    error.value = ''
    status.value = 'idle'
  }
  watch(postcode, clear, { flush: 'sync' })

  async function search() {
    if (isLoading.value) return
    postcode.value = postcode.value.trim()
    clear()
    if (!/^[0-9]{5}$/.test(postcode.value)) {
      status.value = 'invalid'
      error.value = 'Enter a five-digit U.S. ZIP code.'
      return
    }
    const id = ++requestId
    controller = new AbortController()
    const activeController = controller
    const timeout = setTimeout(() => activeController.abort(), 30000)
    status.value = 'loading'
    try {
      const data = await findHotels(postcode.value, activeController.signal)
      if (id !== requestId) return
      result.value = data
      status.value = data.hotels.length ? 'results' : 'empty'
    } catch (failure) {
      if (id !== requestId) return
      status.value = failure.kind || 'failed'
      error.value = activeController.signal.aborted
        ? 'Hotel search timed out. Please try again.' : failure.message
    } finally {
      clearTimeout(timeout)
    }
  }

  function select(placeId) {
    if (result.value?.hotels.some(hotel => hotel.place_id === placeId)) selectedId.value = placeId
  }

  return { postcode, result, selectedId, selectedHotel, status, error, isLoading, search, select, clear }
}
