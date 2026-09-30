export class DiscoveryError extends Error {
  constructor(message, kind = 'failed') {
    super(message)
    this.kind = kind
  }
}

const coordinate = (value, max) => Number.isFinite(value) && Math.abs(value) <= max
const optionalText = (value) => value === null || typeof value === 'string'

export async function findHotels(postcode, signal) {
  if (!/^[0-9]{5}$/.test(postcode)) throw new DiscoveryError('Enter a five-digit U.S. ZIP code.', 'invalid')
  let response
  try {
    response = await fetch(`/api/discovery/hotels?${new URLSearchParams({ postcode })}`, { signal })
  } catch (error) {
    if (signal?.aborted) throw error
    throw new DiscoveryError('Unable to reach hotel search. Check your connection and try again.')
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) {
    const kind = ({ 404: 'unresolved', 422: 'invalid', 429: 'limited' })[response.status] || 'failed'
    throw new DiscoveryError(typeof data?.detail === 'string' ? data.detail : 'Hotel search failed. Please try again.', kind)
  }
  if (data?.provider !== 'geoapify' || data.center?.postcode !== postcode || data.center.country_code !== 'us'
    || !coordinate(data.center.latitude, 90) || !coordinate(data.center.longitude, 180)
    || !optionalText(data.center.locality) || data.radius_meters !== 5000 || data.result_limit !== 20
    || typeof data.limit_reached !== 'boolean' || !Number.isInteger(data.omitted_count) || data.omitted_count < 0
    || !Array.isArray(data.hotels) || data.hotels.length > data.result_limit
    || data.hotels.some(hotel => !hotel || typeof hotel.place_id !== 'string' || !hotel.place_id.trim()
      || !coordinate(hotel.latitude, 90) || !coordinate(hotel.longitude, 180)
      || !optionalText(hotel.name) || !optionalText(hotel.address))
    || new Set(data.hotels.map(hotel => hotel.place_id)).size !== data.hotels.length) {
    throw new DiscoveryError('Hotel search returned an invalid response. Please try again.')
  }
  return data
}
