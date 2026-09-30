<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps({
  result: { type: Object, required: true },
  selectedId: { type: String, default: null },
})
const emit = defineEmits(['select'])
const container = ref(null)
const tileError = ref(false)
let map
let observer
const markers = new Map()

function applySelection() {
  for (const [id, marker] of markers) {
    const selected = id === props.selectedId
    marker.getElement()?.classList.toggle('hotel-pin-selected', selected)
    marker.getElement()?.setAttribute('aria-pressed', String(selected))
    marker.setZIndexOffset(selected ? 1000 : 0)
    if (selected) {
      marker.openPopup()
      map.panTo(marker.getLatLng(), { animate: false })
    }
  }
}

onMounted(() => {
  const { center, hotels, radius_meters: radius } = props.result
  map = L.map(container.value, { scrollWheelZoom: false })
    .fitBounds(L.latLng(center.latitude, center.longitude).toBounds(radius * 2), { padding: [12, 12] })
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).on('tileerror', () => { tileError.value = true }).addTo(map)
  L.circle([center.latitude, center.longitude], {
    radius, color: '#3c7971', weight: 1.5, dashArray: '6 6', fillOpacity: 0.04, interactive: false,
  }).addTo(map)
  L.circleMarker([center.latitude, center.longitude], {
    radius: 5, color: '#17324d', fillOpacity: 1,
  }).bindTooltip(`ZIP ${center.postcode} search center`).addTo(map)
  hotels.forEach((hotel, index) => {
    const name = hotel.name || 'Name not provided'
    const pin = document.createElement('span')
    pin.textContent = String(index + 1)
    const marker = L.marker([hotel.latitude, hotel.longitude], {
      icon: L.divIcon({ html: pin, className: 'hotel-pin', iconSize: [32, 32], iconAnchor: [16, 16] }),
      keyboard: true, title: `${index + 1}. ${name}`, alt: `${index + 1}. ${name}`,
    }).addTo(map)
    const popup = document.createElement('div')
    const heading = document.createElement('strong')
    heading.textContent = `${index + 1}. ${name}`
    const address = document.createElement('p')
    address.textContent = hotel.address || 'Address not provided'
    popup.append(heading, address)
    marker.bindPopup(popup)
    marker.on('click', () => emit('select', hotel.place_id))
    const element = marker.getElement()
    element.setAttribute('aria-label', `Select hotel ${index + 1}: ${name}`)
    element.addEventListener('keydown', event => {
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault()
        event.stopPropagation()
        marker.openPopup()
        emit('select', hotel.place_id)
      }
    })
    markers.set(hotel.place_id, marker)
  })
  observer = new ResizeObserver(() => map.invalidateSize())
  observer.observe(container.value)
  applySelection()
})
watch(() => props.selectedId, applySelection)
onBeforeUnmount(() => {
  observer?.disconnect()
  map?.remove()
  markers.clear()
})
</script>

<template>
  <div class="map-panel">
    <div ref="container" class="hotel-map" role="region" aria-label="Hotel map. Use Tab to reach markers, Enter or Space to select, and arrow keys to pan." />
    <p v-if="tileError" class="map-warning" role="status">Some map imagery could not load. Hotel locations and the list are still available.</p>
    <p class="map-help">Dashed circle: 5 km search area. Dark dot: ZIP center. Moving the map does not change the search.</p>
  </div>
</template>

<style scoped>
.hotel-map { height: 30rem; width: 100%; border-radius: 0.75rem; border: 1px solid #bccad7; z-index: 0; background: #e9edf0; }
.map-help, .map-warning { font-size: 0.8rem; line-height: 1.5; margin: 0.6rem 0; }
.map-warning { color: #7a3d00; }
.hotel-map :deep(.hotel-pin) { border-radius: 50%; background: #fff; border: 2px solid #33756e; color: #225d58; font-size: 14px; font-weight: 800; display: grid; place-items: center; box-shadow: 0 2px 5px #17324d40; }
.hotel-map :deep(.hotel-pin-selected) { background: #276b64; color: white; outline: 3px solid #fff; }
.hotel-map :deep(.hotel-pin:focus-visible) { outline: 4px solid #de7800; }
@media (max-width: 45rem) { .hotel-map { height: 22rem; } }
</style>
