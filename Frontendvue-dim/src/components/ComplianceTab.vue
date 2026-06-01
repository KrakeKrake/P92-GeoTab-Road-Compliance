<template>
  <div>

    <!-- Compliance report — populated by Sprint 3 POST /validate response -->
    <template v-if="report">

      <div class="compliance-result" :class="report.route_compliant ? 'pass' : 'fail'">
        <div class="result-icon">{{ report.route_compliant ? '✓' : '✕' }}</div>
        <div class="result-body">
          <div class="result-title">
            {{ report.route_compliant ? 'ROUTE COMPLIANT' : 'NON-COMPLIANT' }}
          </div>
          <div class="result-detail">{{ report.summary }}</div>
        </div>
      </div>

      <template v-if="errors.length">
        <div class="section-label" style="margin-top:14px">
          Errors ({{ errors.length }})
        </div>
        <div
          v-for="v in errors"
          :key="v.segment_id + v.violation_type"
          class="violation-item"
        >
          <div class="v-dot"></div>
          <div class="v-text">
            <span class="v-road">{{ v.road_name }}</span><br>
            {{ v.detail }}<br>
            <span style="color:var(--text3)">
              {{ v.violation_type }} · {{ v.vehicle_value }} vs {{ v.limit_value }}
            </span>
          </div>
        </div>
      </template>

      <template v-if="warnings.length">
        <div class="section-label" style="margin-top:14px">
          Warnings ({{ warnings.length }})
        </div>
        <div
          v-for="v in warnings"
          :key="v.segment_id + v.violation_type"
          class="violation-item warn-item"
        >
          <div class="v-dot" style="background:var(--warn)"></div>
          <div class="v-text">
            <span class="v-road">{{ v.road_name }}</span><br>
            {{ v.detail }}
          </div>
        </div>
      </template>

    </template>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <div class="empty-state-icon">✅</div>
      <div class="empty-state-title">No compliance report yet</div>
      <div class="empty-state-sub">
        Plan a route and select a vehicle to generate a compliance report against NHVR regulations.
      </div>
    </div>

    <div class="divider"></div>
    <div class="section-label">NHVR Reference</div>
    <div class="nhvr-ref-box">
      Heavy Vehicle National Law (HVNL)<br>
      Mass, Dimension and Loading Requirements<br>
      Schedule 2 — Height Limits by Vehicle Category<br>
      <a
        href="https://www.nhvr.gov.au/road-access/mass-limits"
        target="_blank"
        style="color:var(--accent)"
      >
        nhvr.gov.au/road-access/mass-limits
      </a>
    </div>

  </div>
</template>

<script>
export default {
  name: 'ComplianceTab',

  props: {
    // ComplianceReport object from main.py POST /validate
    report: { type: Object, default: null },
  },

  computed: {
    errors() {
      return (this.report?.violations || []).filter(v => v.severity === 'error')
    },
    warnings() {
      return (this.report?.violations || []).filter(v => v.severity === 'warning')
    },
  },
}
</script>
