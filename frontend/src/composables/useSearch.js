import { ref } from 'vue'
import { searchStays } from '../api/stays.js'

export function useSearch() {
  const hotelName = ref('')
  const searchedName = ref('')
  const stays = ref([])
  const error = ref('')
  const hasSearched = ref(false)
  const isLoading = ref(false)
  let request = 0
  function clear() {
    request++
    stays.value = []
    error.value = ''
    hasSearched.value = false
    isLoading.value = false
  }
  async function submitSearch() {
    if (isLoading.value) return
    clear()
    const current = request
    const query = hotelName.value.trim()
    if (!query) { error.value = 'Enter a hotel name to search.'; return }
    isLoading.value = true
    searchedName.value = query
    try {
      const results = await searchStays(query)
      if (current === request) { stays.value = results; hasSearched.value = true }
    } catch (failure) {
      if (current === request) error.value = failure.message
    } finally {
      if (current === request) isLoading.value = false
    }
  }
  return { hotelName, searchedName, stays, error, hasSearched, isLoading, clear, submitSearch }
}
