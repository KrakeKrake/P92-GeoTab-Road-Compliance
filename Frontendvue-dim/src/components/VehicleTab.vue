<template>
  <div>

    <!-- Licence Class -->
    <div class="section-label">Licence Class</div>
    <div class="select-row">
      <div class="sel-wrap">
        <select class="sel" v-model="licenceClass" @change="onLicChange">
          <option value="">— Select licence class —</option>
          <option value="MC">MC — Multi Combination</option>
          <option value="HC">HC — Heavy Combination</option>
          <option value="HR">HR — Heavy Rigid</option>
          <option value="MR">MR — Medium Rigid</option>
          <option value="LR">LR — Light Rigid</option>
        </select>
        <span class="sel-arrow">▾</span>
      </div>
    </div>

    <template v-if="licenceClass">

      <!-- Vehicle Class -->
      <div class="section-label">Vehicle Class</div>
      <div class="select-row">
        <div class="sel-wrap">
          <select class="sel" v-model="vehicleClass" @change="onClassChange">
            <option value="2">Class 2</option>
            <option value="3">Class 3</option>
          </select>
          <span class="sel-arrow">▾</span>
        </div>
      </div>

      <!-- Vehicle Type — from get_types.php -->
      <div class="section-label">Vehicle Type</div>
      <div class="select-row">
        <div class="sel-wrap">
          <select class="sel" v-model="selectedTypeId" @change="onTypeChange" :disabled="loadingTypes">
            <option value="">{{ loadingTypes ? 'Loading...' : '— Select vehicle type —' }}</option>
            <option v-for="t in filteredTypes" :key="t.vehicle_id" :value="t.vehicle_id">
              {{ t.name }}
            </option>
          </select>
          <span class="sel-arrow">▾</span>
        </div>
      </div>

      <template v-if="selectedTypeId">

        <!-- Axle Configuration — from get_configs.php -->
        <div class="section-label">Axle Configuration</div>
        <div class="select-row">
          <div class="sel-wrap">
            <select class="sel" v-model="selectedAxleId" @change="onConfigChange" :disabled="loadingConfigs">
              <option value="">{{ loadingConfigs ? 'Loading...' : '— Select configuration —' }}</option>
              <option v-for="c in configs" :key="c.axle_id" :value="c.axle_id">
                {{ c.config_name }} ({{ c.axle_count }} axles)
              </option>
            </select>
            <span class="sel-arrow">▾</span>
          </div>
        </div>

        <!-- Configuration detail — from get_config_details.php -->
        <template v-if="configDetail">

          <div class="section-label">Configuration Details</div>
          <div class="info-box">
            <table style="width:100%;font-family:var(--mono);font-size:11px;border-collapse:collapse">
              <tbody>
                <tr><td class="info-key">Axles</td><td>{{ configDetail.axle_count }}</td></tr>
                <tr><td class="info-key">Max length</td><td>{{ configDetail.max_length ? configDetail.max_length + ' m' : '—' }}</td></tr>
                <tr><td class="info-key">Default tare</td><td>{{ Number(configDetail.tare).toLocaleString() }} kg</td></tr>
              </tbody>
            </table>
            <table class="mass-table" style="margin-top:8px">
              <thead>
                <tr><th>GML</th><th>CML</th><th>HML</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ configDetail.gml ? configDetail.gml + 't' : '—' }}</td>
                  <td>{{ configDetail.cml ? configDetail.cml + 't' : '—' }}</td>
                  <td :style="{ color: configDetail.hml ? 'var(--accent)' : 'inherit' }">
                    {{ configDetail.hml ? configDetail.hml + 't' : '—' }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Mass Scheme & Payload -->
          <div class="section-label">Mass Scheme &amp; Payload</div>
          <div class="select-row">
            <div class="sel-wrap">
              <div class="sel-label">Mass Scheme</div>
              <select class="sel" v-model="massScheme" @change="runCheck">
                <option value="gml" :disabled="!configDetail.gml">GML — General Mass Limits</option>
                <option value="cml" :disabled="!configDetail.cml">CML — Concessional</option>
                <option value="hml" :disabled="!configDetail.hml">HML — Higher Mass Limits</option>
              </select>
              <span class="sel-arrow">▾</span>
            </div>
          </div>

          <div class="input-row">
            <div class="input-wrap">
              <div class="input-label">Tare Weight</div>
              <input
                class="input-field"
                type="number"
                min="0"
                step="100"
                v-model.number="tare"
                :style="{ borderColor: tareOverridden ? 'var(--warn)' : '' }"
              >
              <div
                class="input-unit"
                :style="{ color: tareOverridden ? 'var(--warn)' : '', cursor: tareOverridden ? 'pointer' : '' }"
                @click="tareOverridden ? resetTare() : null"
              >
                {{ tareOverridden ? 'kg — overridden (tap to reset)' : 'kg — from database' }}
              </div>
            </div>
            <div class="input-wrap">
              <div class="input-label">Payload</div>
              <input
                class="input-field"
                type="number"
                min="0"
                step="100"
                v-model.number="payload"
                placeholder="0"
              >
              <div class="input-unit">kg</div>
            </div>
          </div>

          <!-- Mass check result -->
          <div v-if="checkResult" class="compliance-result" :class="checkResult.type">
            <div class="result-icon">{{ checkResult.icon }}</div>
            <div class="result-body">
              <div class="result-title">{{ checkResult.title }}</div>
              <div class="result-detail">{{ checkResult.detail }}</div>
            </div>
          </div>

          <!-- Axle Groups -->
          <div class="section-label">Axle Groups</div>
          <table class="mass-table">
            <thead>
              <tr><th>Axle Group</th><th>Limit (kg)</th></tr>
            </thead>
            <tbody>
              <tr v-for="g in configDetail.groups" :key="g.group_name">
                <td>{{ g.group_name }}</td>
                <td>{{ Number(g.group_limit).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>

          <button class="cta" style="margin-top:14px" @click="applyVehicle">
            Apply Vehicle &amp; Check Route
          </button>

        </template>

        <div v-else-if="loadingDetail" class="empty-msg">Loading configuration...</div>
        <div v-else-if="error" class="empty-msg" style="color:var(--danger)">{{ error }}</div>

      </template>

    </template>

    <!-- Empty state before licence selected -->
    <div v-else class="empty-state" style="margin-top:12px">
      <div class="empty-state-icon">🚛</div>
      <div class="empty-state-title">Select your licence class</div>
      <div class="empty-state-sub">
        Your licence class determines which vehicle types and configurations are available.
      </div>
    </div>

  </div>
</template>

<script>
// Licence class → allowed vehicle_type IDs (Victorian licence rules)
const LICENCE_TYPES = {
  LR: [1],
  MR: [1],
  HR: [1],
  HC: [1, 2, 11, 12, 13],
  MC: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13],
}

export default {
  name: 'VehicleTab',
  emits: ['applied'],

  data() {
    return {
      // Selection state
      licenceClass:    '',
      vehicleClass:    '2',
      selectedTypeId:  '',
      selectedAxleId:  '',

      // API data
      types:        [],
      configs:      [],
      configDetail: null,

      // Loading / error
      loadingTypes:   false,
      loadingConfigs: false,
      loadingDetail:  false,
      error:          null,

      // Mass & payload
      massScheme:     'gml',
      tare:           0,
      payload:        0,
      defaultTare:    0,
      tareOverridden: false,
      checkResult:    null,
    }
  },

  computed: {
    filteredTypes() {
      const allowed = LICENCE_TYPES[this.licenceClass] || []
      return this.types.filter(t => allowed.includes(t.vehicle_id))
    },
  },

  watch: {
    tare()    { this.tareOverridden = this.tare !== this.defaultTare; this.runCheck() },
    payload() { this.runCheck() },
  },

  methods: {

    // ── API CALLS ─────────────────────────────────────────────────────────

    onLicChange() {
      this.selectedTypeId = ''
      this.selectedAxleId = ''
      this.configDetail   = null
      this.types          = []
      this.configs        = []
      this.checkResult    = null
      if (this.licenceClass) this.loadTypes()
    },

    onClassChange() {
      this.selectedTypeId = ''
      this.selectedAxleId = ''
      this.configDetail   = null
      this.configs        = []
      this.checkResult    = null
      this.loadTypes()
    },

    // GET get_types.php?class_id=X
    async loadTypes() {
      this.loadingTypes = true
      this.error = null
      try {
        const res    = await fetch(`get_types.php?class_id=${this.vehicleClass}`)
        this.types   = await res.json()
      } catch {
        this.error = 'Failed to load vehicle types.'
        this.types = []
      } finally {
        this.loadingTypes = false
      }
    },

    onTypeChange() {
      this.selectedAxleId = ''
      this.configDetail   = null
      this.configs        = []
      this.checkResult    = null
      if (this.selectedTypeId) this.loadConfigs()
    },

    // GET get_configs.php?vehicle_id=X
    async loadConfigs() {
      this.loadingConfigs = true
      this.error = null
      try {
        const res     = await fetch(`get_configs.php?vehicle_id=${this.selectedTypeId}`)
        this.configs  = await res.json()
      } catch {
        this.error   = 'Failed to load configurations.'
        this.configs = []
      } finally {
        this.loadingConfigs = false
      }
    },

    onConfigChange() {
      this.configDetail = null
      this.checkResult  = null
      if (this.selectedAxleId) this.loadConfigDetails()
    },

    // GET get_config_details.php?axle_id=X
    async loadConfigDetails() {
      this.loadingDetail = true
      this.error = null
      try {
        const res          = await fetch(`get_config_details.php?axle_id=${this.selectedAxleId}`)
        this.configDetail  = await res.json()
        this.defaultTare   = Number(this.configDetail.tare)
        this.tare          = this.defaultTare
        this.tareOverridden = false
        // Set first available mass scheme
        if (!this.configDetail.gml) {
          this.massScheme = this.configDetail.hml ? 'hml' : 'cml'
        } else {
          this.massScheme = 'gml'
        }
        this.runCheck()
      } catch {
        this.error        = 'Failed to load configuration details.'
        this.configDetail = null
      } finally {
        this.loadingDetail = false
      }
    },

    // ── MASS CHECK ────────────────────────────────────────────────────────

    runCheck() {
      if (!this.configDetail) return
      const gross  = this.tare + this.payload
      const grossT = (gross / 1000).toFixed(2)
      const limit  = this.configDetail[this.massScheme]

      if (!limit) {
        this.checkResult = {
          type: 'warn', icon: '—',
          title: 'SCHEME N/A',
          detail: `${this.massScheme.toUpperCase()} is not applicable for this configuration.`
        }
        return
      }
      const limitKg  = limit * 1000
      const headroom = (limit - gross / 1000).toFixed(2)
      const over     = (gross / 1000 - limit).toFixed(2)

      if (gross <= limitKg) {
        this.checkResult = {
          type: 'pass', icon: '✓',
          title: `PASS — ${this.massScheme.toUpperCase()}`,
          detail: `Gross ${grossT}t within ${this.massScheme.toUpperCase()} limit of ${limit}t (${headroom}t headroom).`
        }
      } else {
        this.checkResult = {
          type: 'fail', icon: '✕',
          title: `FAIL — ${this.massScheme.toUpperCase()}`,
          detail: `Gross ${grossT}t exceeds ${this.massScheme.toUpperCase()} limit of ${limit}t by ${over}t.`
        }
      }
    },

    resetTare() {
      this.tare           = this.defaultTare
      this.tareOverridden = false
    },

    // ── APPLY ─────────────────────────────────────────────────────────────

    applyVehicle() {
      if (!this.configDetail) {
        alert('Please select a vehicle configuration.')
        return
      }
      this.$emit('applied', {
        axle_id:    this.selectedAxleId,
        tare_kg:    this.tare,
        payload_kg: this.payload,
        gross_kg:   this.tare + this.payload,
        mass_class: this.massScheme.toUpperCase(),
        gml:        this.configDetail.gml,
        cml:        this.configDetail.cml,
        hml:        this.configDetail.hml,
      })
    },
  },
}
</script>