<template>
  <div>
    <!-- TOP BAR -->
    <div class="topbar">
      <div class="logo">
        HeavyRoute
      </div>

      <div class="topbar-sep"></div>

      <div class="status-pill">
        <div class="status-dot"></div>
        NHVR Compliance System
      </div>

      <div class="topbar-right">
        <UserChip />
      </div>
    </div>

    <!-- MAIN -->
    <div class="main">
      <!-- MAP -->
      <div class="map-area">
        <div id="map"></div>

        <div class="map-empty" id="mapEmpty">
          <div class="map-empty-icon">🗺️</div>
          <div class="map-empty-text">
            Enter origin and destination to plan a route
          </div>
        </div>

        <div class="map-attr">
          © OpenStreetMap contributors
        </div>
      </div>

      <!-- SIDE PANEL -->
      <div class="panel">
        <div class="tabs">
          <div class="tab active" @click="switchTab('route', $event)">Route</div>
          <div class="tab" @click="switchTab('vehicle', $event)">Vehicle</div>
          <div class="tab" @click="switchTab('compliance', $event)">Compliance</div>
          <div class="tab" @click="switchTab('profile', $event)">Profile</div>
        </div>

        <div class="panel-body">
          <!-- ROUTE TAB -->
          <div class="tab-content active" id="tab-route">
            <div class="steps">
              <div class="step active" id="step1">
                <span class="step-num">1</span>Route
              </div>
              <div class="step" id="step2">
                <span class="step-num">2</span>Vehicle
              </div>
              <div class="step" id="step3">
                <span class="step-num">3</span>Check
              </div>
            </div>

            <div class="section-label">Origin &amp; Destination</div>

            <div class="route-inputs">
              <div class="search-box">
                <span class="search-icon">●</span>
                <input
                  class="search-input"
                  id="originInput"
                  placeholder="Enter origin address"
                />
              </div>

              <div class="search-box">
                <span class="search-icon">↑</span>
                <input
                  class="search-input"
                  id="destInput"
                  placeholder="Enter destination"
                />
              </div>

              <div class="swap-btn" @click="swapInputs" title="Swap">
                ⇅
              </div>
            </div>

            <button class="cta" @click="planRoute" id="planBtn">
              Plan Route
            </button>

            <div id="routeSummary" style="display:none">
              <div class="divider"></div>

              <div class="section-label">Route Summary</div>

              <div class="stats-row">
                <div class="stat-card">
                  <div class="stat-value" id="routeDistance">—</div>
                  <div class="stat-label">km</div>
                </div>

                <div class="stat-card">
                  <div class="stat-value" id="routeTime">—</div>
                  <div class="stat-label">Est. time</div>
                </div>

                <div class="stat-card">
                  <div class="stat-value" id="routeViolations">—</div>
                  <div class="stat-label">Violations</div>
                </div>
              </div>

              <div id="routeComplianceResult"></div>
              <div id="violationsList"></div>

              <button
                class="cta secondary"
                style="margin-top:4px"
                @click="switchTabByName('compliance')"
              >
                View Full Compliance Report
              </button>
            </div>

            <div id="routePlaceholder">
              <div class="divider"></div>

              <div class="empty-state">
                <div class="empty-state-icon">📍</div>
                <div class="empty-state-title">No route planned</div>
                <div class="empty-state-sub">
                  Enter your origin and destination above.<br />
                  Make sure your vehicle profile is set before checking compliance.
                </div>
              </div>
            </div>
          </div>

          <!-- VEHICLE TAB -->
          <div class="tab-content" id="tab-vehicle">
            <VehicleTab />
          </div>

          <!-- COMPLIANCE TAB -->
          <div class="tab-content" id="tab-compliance">
            <div id="complianceReport">
              <div class="empty-state">
                <div class="empty-state-icon">✅</div>
                <div class="empty-state-title">No compliance report yet</div>
                <div class="empty-state-sub">
                  Plan a route and select a vehicle to generate a compliance report against NHVR regulations.
                </div>
              </div>
            </div>

            <div class="divider"></div>

            <div class="section-label">NHVR Reference</div>

            <div class="nhvr-ref-box">
              Heavy Vehicle National Law (HVNL)<br />
              Mass, Dimension and Loading Requirements<br />
              Schedule 2 — Height Limits by Vehicle Category<br />
              <span style="color:var(--accent)">
                nhvr.gov.au/road-access/mass-limits
              </span>
            </div>
          </div>

          <!-- PROFILE TAB -->
          <div class="tab-content" id="tab-profile">
            <div class="profile-header">
              <div class="profile-avatar" id="profileAvatar">?</div>
              <div>
                <div class="profile-name" id="profileName">Not signed in</div>
                <div class="profile-licence" id="profileLicence">
                  Sign in to save vehicles and preferences
                </div>
              </div>
            </div>

            <div class="section-label">Saved Vehicles</div>

            <div id="savedVehiclesList">
              <div class="empty-state">
                <div class="empty-state-icon">💾</div>
                <div class="empty-state-title">No saved vehicles</div>
                <div class="empty-state-sub">
                  Sign in and configure a vehicle to save it here for quick access.
                </div>
              </div>
            </div>

            <button class="cta secondary" id="saveVehicleBtn" style="display:none">
              + Save Current Vehicle
            </button>

            <div class="divider"></div>

            <div class="section-label">Account</div>

            <div id="accountBox">
              <div class="empty-state">
                <div class="empty-state-icon">👤</div>
                <div class="empty-state-title">Sign in required</div>
                <div class="empty-state-sub">
                  User profiles and saved data will be available once authentication is implemented in Sprint 3.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import UserChip from '../components/UserChip.vue'
import VehicleTab from '../components/VehicleTab.vue'

function switchTab(id, event) {
  document.querySelectorAll('.tab-content').forEach((tab) => {
    tab.classList.remove('active')
  })

  document.querySelectorAll('.tab').forEach((tab) => {
    tab.classList.remove('active')
  })

  document.getElementById('tab-' + id).classList.add('active')
  event.currentTarget.classList.add('active')
}

function switchTabByName(id) {
  const tabs = document.querySelectorAll('.tab')
  const tabIndex = {
    route: 0,
    vehicle: 1,
    compliance: 2,
    profile: 3,
  }

  document.querySelectorAll('.tab-content').forEach((tab) => {
    tab.classList.remove('active')
  })

  document.querySelectorAll('.tab').forEach((tab) => {
    tab.classList.remove('active')
  })

  document.getElementById('tab-' + id).classList.add('active')
  tabs[tabIndex[id]].classList.add('active')
}

function planRoute() {
  const origin = document.getElementById('originInput').value.trim()
  const dest = document.getElementById('destInput').value.trim()

  if (!origin || !dest) {
    alert('Please enter both an origin and destination.')
    return
  }

  alert(
    'Route planning will connect to the pgRouting backend in Sprint 3.\\nOrigin: ' +
      origin +
      '\\nDestination: ' +
      dest
  )
}

function swapInputs() {
  const origin = document.getElementById('originInput')
  const dest = document.getElementById('destInput')

  const temp = origin.value
  origin.value = dest.value
  dest.value = temp
}
</script>