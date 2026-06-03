<template>
  <div id="app">

    <!-- TOP BAR -->
    <header class="topbar">
      <div class="logo">HeavyRoute</div>
      <div class="topbar-sep"></div>
      <div class="status-pill">
        <div class="status-dot"></div>
        NHVR Compliance System
      </div>
      <div class="topbar-right">
        <UserChip />
      </div>
    </header>

    <!-- MAIN LAYOUT -->
    <div class="main">

      <!-- MAP -->
      <MapView
        :route-geojson="routeGeojson"
        :violations="route.violations"
      />

      <!-- SIDE PANEL -->
      <div class="panel">
        <div class="tabs">
          <div
            v-for="tab in tabs"
            :key="tab.id"
            class="tab"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </div>
        </div>

        <div class="panel-body">
          <RouteTab
            v-if="activeTab === 'route'"
            :route="route"
            :route-planned="routePlanned"
            :vehicle-applied="vehicleApplied"
            @plan="onPlanRoute"
            @view-compliance="activeTab = 'compliance'"
          />
          <VehicleTab
            v-if="activeTab === 'vehicle'"
            @applied="onVehicleApplied"
          />
          <ComplianceTab
            v-if="activeTab === 'compliance'"
            :report="complianceReport"
          />
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import UserChip from '../components/UserChip.vue'
import MapView from '../components/MapView.vue'
import RouteTab from '../components/RouteTab.vue'
import VehicleTab from '../components/VehicleTab.vue'
import ComplianceTab from '../components/ComplianceTab.vue'

export default {
  name: 'App',
  components: { MapView, RouteTab, VehicleTab, ComplianceTab, UserChip },

  data() {
    return {
      activeTab: 'route',
      tabs: [
        { id: 'route',       label: 'Route'      },
        { id: 'vehicle',     label: 'Vehicle'    },
        { id: 'compliance',  label: 'Compliance' },
      ],

      route: {
        distanceKm:  null,
        durationMin: null,
        violations:  [],
      },
      routeGeojson:     null,
      routePlanned:     false,
      vehicleApplied:   false,
      complianceReport: null,

      user: null,
    }
  },

  methods: {
   
    onPlanRoute({ origin, destination, vehicleProfile }) {
      console.log('Plan route:', origin, '→', destination, vehicleProfile)

    },

    // Emitted by VehicleTab when Apply is clicked
    // TODO Sprint 3: trigger compliance check
    onVehicleApplied(vehicleProfile) {
      this.vehicleApplied = true
      this.activeTab = 'route'
      console.log('Vehicle applied:', vehicleProfile)
      // if (this.routeGeojson) this.runComplianceCheck(vehicleProfile)
    },

    // Called with response from POST /validate (main.py FastAPI)
    showComplianceReport(report) {
      this.complianceReport  = report
      this.route.violations  = report.violations
      this.activeTab         = 'compliance'
    },
  },
}
</script>

<style>
@import "../assets/navigation.css";

</style>