export async function lookupZip(postcode) {
  const query = typeof postcode === 'string' ? postcode.trim() : ''
  if (!/^[0-9]{5}$/.test(query)) {
    throw new Error('Enter a five-digit U.S. ZIP code.')
  }
  const parameters = new URLSearchParams({ postcode: query })
  let response
  try {
    response = await fetch(`/api/zip-location?${parameters}`)
  } catch {
    throw new Error('Unable to reach the ZIP lookup service.')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new Error(typeof data?.detail === 'string'
      ? data.detail
      : 'The ZIP lookup could not be completed.')
  }
  if (data?.postcode !== query || data.country_code !== 'us' || !Number.isFinite(data.latitude)
    || !Number.isFinite(data.longitude)) {
    throw new Error('The ZIP lookup service returned an invalid response.')
  }
  return data
}
