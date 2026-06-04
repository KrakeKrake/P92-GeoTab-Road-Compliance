<script setup lang="ts">
import { onMounted, ref, toRaw, watch } from "vue";
import maplibregl from "maplibre-gl";
import { getRoute, get_geo } from "../../scripts/api.ts";
import type { wayPoint } from "../../scripts/api.ts";

const mapContainer = ref<HTMLElement | null>(null);
const route = ref<wayPoint[]>([]);
const geos = ref<[number, number][]>([]);
const osm_id_1 = ref<number | null>(null);
const osm_id_2 = ref<number | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

// Keep map ref outside onMounted so watchers can access it
let map: maplibregl.Map | null = null;
let mapLoaded = false;

function updateMapSource(coordinates: [number, number][]) {
    if (!map || !mapLoaded) return;
    const source = map.getSource("route") as
        | maplibregl.GeoJSONSource
        | undefined;
    if (!source) return;

    source.setData({
        type: "Feature",
        geometry: {
            type: "LineString",
            coordinates,
        },
        properties: {},
    });

    // Fit the map to the new route (filter out any NaN coords defensively)
    const valid = coordinates.filter(
        ([lng, lat]) => isFinite(lng) && isFinite(lat),
    );
    if (valid.length > 0) {
        const bounds = valid.reduce(
            (b, coord) => b.extend(coord),
            new maplibregl.LngLatBounds(valid[0], valid[0]),
        );
        map.fitBounds(bounds, { padding: 60, maxZoom: 16 });
    }
}

onMounted(() => {
    map = new maplibregl.Map({
        container: mapContainer.value!,
        style: "https://tiles.openfreemap.org/styles/liberty",
        center: [144.9631, -37.8136],
        zoom: 10,
    });

    map.on("load", () => {
        mapLoaded = true;

        // Add an empty source — will be updated via setData() after API calls
        map!.addSource("route", {
            type: "geojson",
            data: {
                type: "Feature",
                geometry: { type: "LineString", coordinates: [] },
                properties: {},
            },
        });

        map!.addLayer({
            id: "route",
            type: "line",
            source: "route",
            paint: {
                "line-color": "#ff0000",
                "line-width": 4,
            },
        });

        // In case geos were loaded before the map finished initialising
        if (geos.value.length > 0) {
            updateMapSource(toRaw(geos.value));
        }
    });
});

// Reactively update the map whenever geos changes
watch(geos, (newGeos) => {
    updateMapSource(toRaw(newGeos));
});

async function onSubmitOSM() {
    if (osm_id_1.value === null || osm_id_2.value === null) {
        error.value = "Please enter both OSM IDs";
        return;
    }
    loading.value = true;
    error.value = null;
    try {
        route.value = await getRoute(osm_id_1.value, osm_id_2.value);
        geos.value = await get_geo(route.value);
    } catch (e: unknown) {
        error.value = e instanceof Error ? e.message : "Failed to fetch route";
        console.error(e);
    } finally {
        loading.value = false;
    }
}
</script>

<template>
    <div class="map-wrapper">
        <div class="map-controls">
            <input
                v-model.number="osm_id_1"
                type="number"
                placeholder="Origin OSM ID"
            />
            <input
                v-model.number="osm_id_2"
                type="number"
                placeholder="Destination OSM ID"
            />
            <button @click="onSubmitOSM" :disabled="loading">
                {{ loading ? "Loading…" : "Get Route" }}
            </button>
            <span v-if="error" class="map-error">{{ error }}</span>
        </div>
        <div ref="mapContainer" class="map-container" />
    </div>
</template>

<style scoped>
.map-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
}
.map-controls {
    display: flex;
    gap: 8px;
    align-items: center;
    padding: 8px;
    background: #1a1a2e;
}
.map-controls input {
    padding: 6px 10px;
    border-radius: 4px;
    border: 1px solid #444;
    background: #2a2a3e;
    color: #fff;
    width: 160px;
}
.map-controls button {
    padding: 6px 16px;
    border-radius: 4px;
    border: none;
    background: #4f6ef7;
    color: #fff;
    cursor: pointer;
}
.map-controls button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}
.map-error {
    color: #ff6b6b;
    font-size: 0.85rem;
}
.map-container {
    flex: 1;
    min-height: 500px;
}
</style>
