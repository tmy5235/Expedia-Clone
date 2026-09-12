export async function searchStays(hotelName) {
  const query = hotelName.trim()
  if (!query) {
    throw new Error('Enter a hotel name.')
  }

  const parameters = new URLSearchParams({ hotel_name: query })
  let response

  try {
    response = await fetch(`/api/stays?${parameters}`)
  } catch {
    throw new Error('Unable to reach the hotel search service.')
  }

  const data = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(data?.detail || 'The hotel search could not be completed.')
  }

  if (!Array.isArray(data)) {
    throw new Error('The hotel search service returned an invalid response.')
  }

  return data
}
