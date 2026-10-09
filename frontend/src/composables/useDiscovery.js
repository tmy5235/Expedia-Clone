import { computed, ref, watch } from 'vue'
import { findLocalFirstHotels, saveLocalHotel, removeLocalHotel } from '../api/localHotels.js'

export function useDiscovery() {
  const postcode = ref('16802')
  const result = ref(null)
  const selectedId = ref(null)
  const status = ref('idle')
  const error = ref('')
  const source = ref(null)
  const savedIds = ref(new Set())
  const pendingIds = ref(new Set())
  const actionFeedback = ref({})
  const hasPending = computed(() => pendingIds.value.size > 0)
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
    source.value = null
    savedIds.value = new Set()
    actionFeedback.value = {}
  }
  watch(postcode, clear, { flush: 'sync' })

  async function search() {
    if (isLoading.value || hasPending.value) return
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
      const data = await findLocalFirstHotels(postcode.value, activeController.signal)
      if (id !== requestId) return
      result.value = data.result
      source.value = data.source
      savedIds.value = new Set(data.savedIds)
      status.value = data.result.hotels.length ? 'results' : 'empty'
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

  function feedback(hotel, text, failed = false) {
    actionFeedback.value = { ...actionFeedback.value,
      [hotel.place_id]: { name: hotel.name || 'Name not provided', text, failed } }
  }

  async function changeLocal(hotel, removing = false) {
    const placeId = hotel.place_id
    if (pendingIds.value.has(placeId) || isLoading.value || !result.value
      || !result.value.hotels.some(item => item.place_id === placeId)
      || savedIds.value.has(placeId) !== removing) return
    const context = result.value.center
    const generation = requestId
    pendingIds.value.add(placeId)
    feedback(hotel, removing ? 'Removing…' : 'Saving…')
    const mutationController = new AbortController()
    const timeout = setTimeout(() => mutationController.abort(), 30000)
    try {
      if (removing) await removeLocalHotel(placeId, mutationController.signal)
      else await saveLocalHotel(hotel, context, mutationController.signal)
      if (generation !== requestId) return
      if (removing) {
        savedIds.value.delete(placeId)
        if (source.value === 'local') {
          result.value = { ...result.value, hotels: result.value.hotels.filter(item => item.place_id !== placeId) }
          if (selectedId.value === placeId) selectedId.value = null
          status.value = result.value.hotels.length ? 'results' : 'empty'
        }
      } else savedIds.value.add(placeId)
      feedback(hotel, removing
        ? 'Removed from your saved hotels.'
        : 'Saved locally. Ready to compare stays.')
    } catch (failure) {
      if (generation !== requestId) return
      feedback(hotel, mutationController.signal.aborted
        ? 'Local change timed out. Search again to confirm saved status before retrying.'
        : failure.message, true)
    } finally {
      clearTimeout(timeout)
      pendingIds.value.delete(placeId)
    }
  }

  return { postcode, result, selectedId, selectedHotel, status, error, isLoading, search, select, clear,
    source, savedIds, pendingIds, hasPending, actionFeedback,
    addLocal: hotel => changeLocal(hotel), removeLocal: hotel => changeLocal(hotel, true) }
}
