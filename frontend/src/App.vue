<script setup>
import { defineAsyncComponent } from 'vue'
import HotelDiscovery from './components/HotelDiscovery.vue'

const BookingDemo = defineAsyncComponent(() => import('./components/BookingDemo.vue'))
const showBookingDemo = new URLSearchParams(window.location.search).get('demo') === 'booking'
</script>

<template>
  <a class="skip-link" href="/#hotel-search">Skip to hotel search</a>
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="/#hotel-search" aria-label="Hotel Finder, hotel search">
        <span class="brand-mark" aria-hidden="true">
          <svg viewBox="0 0 24 24" fill="none"><path d="M4 21V7l8-4 8 4v14M2 21h20M10 21v-5h4v5M8 9h1m6 0h1M8 12h1m6 0h1" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" /></svg>
        </span>
        <span>Hotel Finder</span>
      </a>
      <nav aria-label="Main navigation"><a class="nav-link" href="/#hotel-search">Explore hotels</a><a class="nav-link" href="/#hotel-assistant">Ask about saved hotels</a><a class="nav-link" href="/#about-search">How it works</a></nav>
    </div>
  </header>

  <main>
    <HotelDiscovery v-if="!showBookingDemo" />
    <section v-else class="legacy-page" aria-label="Your stays">
      <h1>Your stays</h1>
      <p><a href="/">Return to hotel discovery</a></p>
      <BookingDemo />
    </section>
  </main>
</template>

<style scoped>
.site-header { background: #fff; border-bottom: 1px solid #e6e8e9; }
.header-inner { width: min(100% - 3rem, 74rem); min-height: 84px; margin: auto; display: flex; justify-content: space-between; align-items: center; gap: 2rem; }
.brand { color: #162f38; text-decoration: none; font-size: 1.45rem; font-weight: 750; letter-spacing: -0.06em; display: inline-flex; align-items: center; gap: 0.65rem; }
.brand-mark { width: 34px; height: 34px; display: grid; place-items: center; color: #215b60; background: #e5eeea; border-radius: 9px; }
.brand-mark svg { width: 25px; height: 25px; }
nav { display: flex; align-items: center; gap: 2rem; }
.nav-link { color: #344e58; font-size: 0.9rem; font-weight: 600; text-decoration: none; }
.nav-link:hover { text-decoration: underline; text-underline-offset: 5px; }
.legacy-page { width: min(100% - 2rem, 74rem); margin: 2rem auto; }
.skip-link { position: absolute; top: -5rem; left: 1rem; background: white; color: #153f45; padding: 0.75rem; z-index: 2000; }
.skip-link:focus { top: 1rem; }
@media (max-width: 40rem) {
  .header-inner { width: calc(100% - 2rem); min-height: 72px; gap: 0.5rem; }
  .brand { font-size: 1.25rem; }
  nav { gap: 1rem; }
  .nav-link { font-size: 0.75rem; }
  nav .nav-link:first-child { display: none; }
}
</style>
