<template>
    <!-- TOP BAR -->
    <header class="topbar">
        <div class="logo">HeavyRoute</div>
        <div class="topbar-right">
            <UserChip />
        </div>
    </header>

    <!-- MAIN LAYOUT -->
    <div class="main">
        <!-- SIDE PANEL — permanent left sidebar -->
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

        <!-- MAP fills remaining space -->
        <Mapping :waypoints="routeWaypoints"></Mapping>
    </div>
</template>

<script>
import MapView from "./MapView.vue";
import Mapping from "../../components/Map_Components/Mapping.vue";
import RouteTab from "./RouteTab.vue";
import VehicleTab from "./VehicleTab.vue";
import ComplianceTab from "./ComplianceTab.vue";
import UserChip from "./UserChip.vue";

export default {
    name: "App",
    components: { MapView, RouteTab, VehicleTab, ComplianceTab, Mapping, UserChip },

    data() {
        return {
            activeTab: "route",
            tabs: [
                { id: "route", label: "Route" },
                { id: "vehicle", label: "Vehicle" },
                { id: "compliance", label: "Compliance" },
            ],

            route: {
                distanceKm: null,
                durationMin: null,
                violations: [],
            },
            routeWaypoints: [],
            routePlanned: false,
            routeLoading: false,
            vehicleApplied: false,
            complianceReport: null,

            user: null,
        };
    },

    methods: {
        async onPlanRoute({ origin, destination, originCoords, destCoords }) {
            this.routeLoading = true;
            this.route = { distanceKm: null, durationMin: null, violations: [] };
            this.routeWaypoints = [];
            this.routePlanned = false;

            try {
                const url = `/api/route?lat1=${originCoords.lat}&lon1=${originCoords.lon}&lat2=${destCoords.lat}&lon2=${destCoords.lon}`;
                const res = await fetch(url);
                const data = await res.json();

                if (!res.ok) {
                    alert(data.error || "Routing failed.");
                    return;
                }

                this.routeWaypoints = data;

                // Estimate distance and duration from waypoints
                let totalCostSec = 0;
                let totalDistM = 0;
                for (const wp of data) {
                    totalCostSec += wp.cost || 0;
                    const dx = (wp.geo_end[0] - wp.geo_start[0]) * 111320 * Math.cos(wp.geo_start[1] * Math.PI / 180);
                    const dy = (wp.geo_end[1] - wp.geo_start[1]) * 110540;
                    totalDistM += Math.sqrt(dx * dx + dy * dy);
                }
                this.route.distanceKm = (totalDistM / 1000).toFixed(1);
                this.route.durationMin = Math.round(totalCostSec / 60);
                this.routePlanned = true;
            } catch (err) {
                alert("Could not connect to the routing service. Make sure the routing server is running.");
            } finally {
                this.routeLoading = false;
            }
        },

        onVehicleApplied(vehicleProfile) {
            this.vehicleApplied = true;
            this.activeTab = "route";
            console.log("Vehicle applied:", vehicleProfile);
        },

        showComplianceReport(report) {
            this.complianceReport = report;
            this.route.violations = report.violations;
            this.activeTab = "compliance";
        },
    },
};
</script>

<style>
@import "./navigation.css";
</style>
