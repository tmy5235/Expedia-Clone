import { DiscoveryError, findHotels } from './discovery.js'

const coordinate = (value, max) => Number.isFinite(value) && Math.abs(value) <= max
const optionalText = value => value === null || typeof value === 'string'
const validHotel = hotel => hotel && typeof hotel.place_id === 'string' && hotel.place_id.trim()
  && optionalText(hotel.name) && optionalText(hotel.address)
  && coordinate(hotel.latitude, 90) && coordinate(hotel.longitude, 180)
const validNight = night => night && /^\d{4}-\d{2}-\d{2}$/.test(night.stay_date)
  && Number.isSafeInteger(night.nightly_rate_cents) && night.nightly_rate_cents >= 0
  && Number.isSafeInteger(night.rooms_available) && night.rooms_available >= 0
const validSavedHotel = hotel => validHotel(hotel) && Array.isArray(hotel.demo_nights)
  && hotel.demo_nights.every(validNight)
  && new Set(hotel.demo_nights.map(night => night.stay_date)).size === hotel.demo_nights.length

async function localRequest(path, options = {}) {
  let response
  try {
    response = await fetch(`/api/local-hotels${path}`, { cache: 'no-store', ...options })
  } catch (error) {
    if (options.signal?.aborted) throw error
    throw new DiscoveryError('Unable to reach local storage. Check your connection and try again.')
  }
  if (options.method === 'DELETE' && response.ok) {
    if (response.status !== 204) invalid()
    return null
  }
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new DiscoveryError(typeof data?.detail === 'string'
    ? data.detail : 'Local storage request failed. Please try again.')
  return data
}

function invalid() {
  throw new DiscoveryError('Local storage returned an invalid response. Please try again.')
}

export async function getLocalHotels(postcode, signal) {
  const data = await localRequest(`?${new URLSearchParams({ postcode })}`, { signal })
  if (data?.source !== 'local' || data.provider !== 'geoapify' || data.radius_meters !== 5000
    || !Array.isArray(data.hotels) || !data.hotels.every(validSavedHotel)
    || new Set(data.hotels.map(hotel => hotel.place_id)).size !== data.hotels.length) invalid()
  if ((data.hotels.length || data.center !== null) && (data.center?.postcode !== postcode || data.center.country_code !== 'us'
    || !coordinate(data.center.latitude, 90) || !coordinate(data.center.longitude, 180)
    || !optionalText(data.center.locality))) invalid()
  return data
}

export async function getSavedIds(placeIds, signal) {
  const data = await localRequest('/status', { method: 'POST', signal,
    headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ place_ids: placeIds }) })
  if (!Array.isArray(data?.saved_ids) || data.saved_ids.some(id => !placeIds.includes(id))
    || new Set(data.saved_ids).size !== data.saved_ids.length) invalid()
  return data.saved_ids
}

export async function findLocalFirstHotels(postcode, signal) {
  const local = await getLocalHotels(postcode, signal)
  if (signal?.aborted) throw new DiscoveryError('Hotel search was cancelled.')
  if (local.hotels.length) return { result: local, source: 'local', savedIds: local.hotels.map(hotel => hotel.place_id) }
  const result = await findHotels(postcode, signal)
  if (signal?.aborted) throw new DiscoveryError('Hotel search was cancelled.')
  // A place saved under another ZIP is still saved: status uses provider ID globally.
  const savedIds = result.hotels.length ? await getSavedIds(result.hotels.map(hotel => hotel.place_id), signal) : []
  return { result, source: 'api', savedIds }
}

export async function saveLocalHotel(hotel, center, signal) {
  const { place_id, name, address, latitude, longitude } = hotel
  const data = await localRequest('', { method: 'POST', signal,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ hotel: { place_id, name, address, latitude, longitude }, center }) })
  if (!validSavedHotel(data) || data.place_id !== place_id) invalid()
  return data
}

export async function removeLocalHotel(placeId, signal) {
  const data = await localRequest(`?${new URLSearchParams({ hotel_id: placeId })}`, { method: 'DELETE', signal })
  if (data !== null) invalid()
}
