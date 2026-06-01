<template>
  <div>

    <!-- Progress steps -->
    <div class="steps">
      <div class="step" :class="step1Class"><span class="step-num">{{ routePlanned ? '✓' : '1' }}</span>Route</div>
      <div class="step" :class="step2Class"><span class="step-num">{{ vehicleApplied ? '✓' : '2' }}</span>Vehicle</div>
      <div class="step" :class="step3Class"><span class="step-num">3</span>Check</div>
    </div>

    <div class="section-label">Origin &amp; Destination</div>
    <div class="route-inputs">
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
          @focus="originFocused = true"
          @blur="originFocused = false"
        >
      </div>
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
          @focus="destFocused = true"
          @blur="destFocused = false"
        >
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
        <div class="result-icon">{{ route.violations.length ? '⚠' : '✓' }}</div>
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
        <div class="empty-state-icon">📍</div>
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
      origin:        '',
      destination:   '',
      originFocused: false,
      destFocused:   false,
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
      // Emit to App.vue which calls the routing API
      this.$emit('plan', {
        origin:      this.origin,
        destination: this.destination,
      })
    },

    swapInputs() {
      ;[this.origin, this.destination] = [this.destination, this.origin]
    },
  },
}
</script>
