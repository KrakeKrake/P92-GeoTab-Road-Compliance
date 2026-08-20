<template>
  <div>

    <!-- Progress steps -->
    <div class="steps">
      <div class="step" :class="step1Class"><span class="step-num">1</span>Route</div>
      <div class="step" :class="step2Class"><span class="step-num">2</span>Vehicle</div>
      <div class="step" :class="step3Class"><span class="step-num">3</span>Check</div>
    </div>

    <div class="section-label">Origin &amp; Destination</div>
    <div class="route-inputs">

      <!-- ORIGIN -->
      <div class="search-box-wrap">
        <div class="search-box" :class="{ focused: originFocused }">
          <span class="search-icon">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <circle cx="6" cy="6" r="4" stroke="currentColor" stroke-width="1.5"/>
              <circle cx="6" cy="6" r="1.5" fill="currentColor"/>
            </svg>
          </span>
          <input
            v-model="origin"
            class="search-input"
            placeholder="Enter origin address"
            autocomplete="off"
            @focus="originFocused = true"
            @blur="originFocused = false; hideOriginSugg()"
            @input="onOriginInput"
          >
        </div>
        <ul v-if="originSuggestions.length" class="sugg-list">
          <li
            v-for="(s, i) in originSuggestions"
            :key="i"
            class="sugg-item"
            @mousedown.prevent="selectOrigin(s)"
          >
            <span class="sugg-primary">{{ s.primary }}</span>
            <span v-if="s.secondary" class="sugg-secondary">{{ s.secondary }}</span>
          </li>
        </ul>
      </div>

      <!-- DESTINATION -->
      <div class="search-box-wrap">
        <div class="search-box" :class="{ focused: destFocused }">
          <span class="search-icon">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M7 12V2M4 5l3-3 3 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <input
            v-model="destination"
            class="search-input"
            placeholder="Enter destination"
            autocomplete="off"
            @focus="destFocused = true"
            @blur="destFocused = false; hideDestSugg()"
            @input="onDestInput"
          >
        </div>
        <ul v-if="destSuggestions.length" class="sugg-list">
          <li
            v-for="(s, i) in destSuggestions"
            :key="i"
            class="sugg-item"
            @mousedown.prevent="selectDest(s)"
          >
            <span class="sugg-primary">{{ s.primary }}</span>
            <span v-if="s.secondary" class="sugg-secondary">{{ s.secondary }}</span>
          </li>
        </ul>
      </div>

      <div class="swap-btn" title="Swap" @click="swapInputs">⇅</div>
    </div>

    <button class="cta" @click="planRoute">
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
        <path d="M2 7h10M8 3l4 4-4 4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      Plan Route
    </button>

    <!-- Route result — shown after backend responds -->
    <template v-if="routePlanned">
      <div class="divider"></div>
      <div class="section-label">Route Summary</div>
      <div class="stats-row">
        <div class="stat-card">
          <div class="stat-value">{{ route.distanceKm ?? '—' }}</div>
          <div class="stat-label">km</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formattedDuration }}</div>
          <div class="stat-label">Est. time</div>
        </div>
        <div class="stat-card">
          <div class="stat-value" :style="{ color: route.violations.length ? 'var(--danger)' : '#1e8e3e' }">
            {{ route.violations.length }}
          </div>
          <div class="stat-label">Violations</div>
        </div>
      </div>

      <div class="compliance-result" :class="route.violations.length ? 'fail' : 'pass'">
        <div class="result-icon">{{ route.violations.length ? '!' : '✓' }}</div>
        <div class="result-body">
          <div class="result-title">
            {{ route.violations.length ? 'NON-COMPLIANT ROUTE' : 'ROUTE COMPLIANT' }}
          </div>
          <div class="result-detail">
            {{ route.violations.length
              ? `${route.violations.length} violation(s) detected. Review before departure.`
              : 'No violations detected across this route.' }}
          </div>
        </div>
      </div>

      <div
        v-for="v in route.violations"
        :key="v.segment_id"
        class="violation-item"
        :class="{ 'warn-item': v.severity === 'warning' }"
      >
        <div class="v-dot" :style="v.severity === 'warning' ? { background: 'var(--warn)' } : {}"></div>
        <div class="v-text">
          <span class="v-road">{{ v.road_name }}</span><br>
          {{ v.detail }}<br>
          <span style="color:var(--text3)">Segment {{ v.segment_id }}</span>
        </div>
      </div>

      <button class="cta secondary" style="margin-top:4px" @click="$emit('view-compliance')">
        View Full Compliance Report
      </button>
    </template>

    <!-- Empty state -->
    <template v-else>
      <div class="divider"></div>
      <div class="empty-state">

        <div class="empty-state-title">No route planned</div>
        <div class="empty-state-sub">
          Enter your origin and destination above.<br>
          Set your vehicle profile before checking compliance.
        </div>
      </div>
    </template>

  </div>
</template>

<script>
export default {
  name: 'RouteTab',

  props: {
    route:          { type: Object,  required: true },
    routePlanned:   { type: Boolean, default: false },
    vehicleApplied: { type: Boolean, default: false },
  },

  emits: ['plan', 'view-compliance'],

  data() {
    return {
      origin:            '',
      destination:       '',
      originCoords:      null,   // { lat, lon } from Nominatim
      destCoords:        null,
      originFocused:     false,
      destFocused:       false,
      originSuggestions: [],
      destSuggestions:   [],
      userLat:           null,
      userLon:           null,
      originTimer:       null,
      destTimer:         null,
    }
  },

  mounted() {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          this.userLat = pos.coords.latitude;
          this.userLon = pos.coords.longitude;
        },
        () => {} // silently ignore — location bias is optional
      );
    }
  },

  computed: {
    formattedDuration() {
      if (!this.route.durationMin) return '—'
      const hrs  = Math.floor(this.route.durationMin / 60)
      const mins = this.route.durationMin % 60
      return hrs > 0 ? `${hrs}h ${mins}m` : `${mins}m`
    },
    step1Class() { return this.routePlanned   ? 'done'   : 'active' },
    step2Class() { return this.vehicleApplied ? 'done'   : (this.routePlanned ? 'active' : '') },
    step3Class() { return (this.routePlanned && this.vehicleApplied) ? 'active' : '' },
  },

  methods: {
    planRoute() {
      if (!this.origin || !this.destination) {
        alert('Please enter both an origin and destination.')
        return
      }
      if (!this.originCoords || !this.destCoords) {
        alert('Please select a location from the suggestions so we can get the coordinates.')
        return
      }
      this.$emit('plan', {
        origin:      this.origin,
        destination: this.destination,
        originCoords: this.originCoords,
        destCoords:   this.destCoords,
      })
    },

    swapInputs() {
      ;[this.origin,       this.destination] = [this.destination,  this.origin]
      ;[this.originCoords, this.destCoords]  = [this.destCoords,   this.originCoords]
    },

    onOriginInput() {
      this.originCoords = null;  // coords no longer valid — user is editing manually
      clearTimeout(this.originTimer);
      this.originTimer = setTimeout(() => this.fetchSuggestions(this.origin, 'origin'), 300);
    },

    onDestInput() {
      this.destCoords = null;    // coords no longer valid — user is editing manually
      clearTimeout(this.destTimer);
      this.destTimer = setTimeout(() => this.fetchSuggestions(this.destination, 'dest'), 300);
    },

    async fetchSuggestions(query, field) {
      const target = field === 'origin' ? 'originSuggestions' : 'destSuggestions';

      if (!query || query.length < 2) {
        this[target] = [];
        return;
      }

      let url = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=5&countrycodes=au`;

      if (this.userLat !== null && this.userLon !== null) {
        // Bias results toward the user's location with a ~165 km viewbox
        const d = 1.5;
        const vb = `${this.userLon - d},${this.userLat + d},${this.userLon + d},${this.userLat - d}`;
        url += `&viewbox=${vb}&bounded=0`;
      }

      try {
        const res = await fetch(url);
        if (!res.ok) return;
        const data = await res.json();
        this[target] = data.map(item => {
          const addr    = item.address || {};
          const primary = item.display_name.split(', ')[0];
          const suburb  = addr.suburb || addr.town || addr.village || addr.city_district || '';
          const city    = addr.city || addr.county || addr.state_district || '';
          const state   = addr.state || '';
          const secondary = [suburb, city, state].filter(Boolean).join(', ');
          const label   = [primary, secondary].filter(Boolean).join(', ');
          return { primary, secondary, label, lat: parseFloat(item.lat), lon: parseFloat(item.lon) };
        });
      } catch {
        // network error — leave suggestions unchanged
      }
    },

    selectOrigin(s) {
      this.origin       = s.label;
      this.originCoords = { lat: s.lat, lon: s.lon };
      this.originSuggestions = [];
    },

    selectDest(s) {
      this.destination = s.label;
      this.destCoords  = { lat: s.lat, lon: s.lon };
      this.destSuggestions = [];
    },

    hideOriginSugg() {
      setTimeout(() => { this.originSuggestions = []; }, 150);
    },

    hideDestSugg() {
      setTimeout(() => { this.destSuggestions = []; }, 150);
    },
  },
}
</script>

<style scoped>
.search-box-wrap {
  position: relative;
}

.sugg-list {
  position: absolute;
  top: calc(100% - 6px); /* sit flush under the search-box (which has margin-bottom: 6px) */
  left: 0;
  right: 0;
  z-index: 200;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  border-top: none;
  border-radius: 0 0 10px 10px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
  list-style: none;
  padding: 0;
  overflow: hidden;
}

.sugg-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
  padding: 8px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.1s;
}
.sugg-item:last-child { border-bottom: none; }
.sugg-item:hover { background: rgba(26, 115, 232, 0.06); }

.sugg-primary {
  font-size: 12px;
  color: #202124;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sugg-secondary {
  font-size: 10px;
  color: #9aa0a6;
  font-family: 'DM Mono', monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
