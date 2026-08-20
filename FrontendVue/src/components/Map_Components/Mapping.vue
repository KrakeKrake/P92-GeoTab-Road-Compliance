<script setup lang="ts">
import { onMounted, ref, toRaw, watch } from "vue";
import maplibregl from "maplibre-gl";
import { getRoute } from "../../scripts/api.ts";
import type { wayPoint } from "../../scripts/api.ts";

const props = defineProps<{
    waypoints?: wayPoint[];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const route = ref<wayPoint[]>([]);
const osm_id_1 = ref<number | null>(null);
const osm_id_2 = ref<number | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const userLngLat = ref<[number, number] | null>(null);

let map: maplibregl.Map | null = null;
let mapLoaded = false;
let popup: maplibregl.Popup | null = null;
let userMarker: maplibregl.Marker | null = null;

const TAG_NAMES: Record<number, string> = {
    101: "motorway",
    102: "motorway_link",
    104: "trunk",
    105: "trunk_link",
    106: "primary",
    107: "primary_link",
    108: "secondary",
    109: "secondary_link",
    110: "tertiary",
    111: "tertiary_link",
    112: "residential",
    113: "living_street",
    114: "service",
    117: "unclassified",
};

function buildFeatureCollection(waypoints: wayPoint[]) {
    return {
        type: "FeatureCollection" as const,
        features: waypoints.map((wp) => ({
            type: "Feature" as const,
            geometry: {
                type: "LineString" as const,
                coordinates: [
                    [wp.geo_start[0], wp.geo_start[1]],
                    [wp.geo_end[0], wp.geo_end[1]],
                ],
            },
            properties: {
                seq: wp.seq,
                name: wp.name ?? "(unnamed)",
                cost: wp.cost,
                tag_id: wp.tag_id,
                road_type: TAG_NAMES[wp.tag_id] ?? "unknown",
                osm_id: wp.osm_id,
                edge_id: wp.edge_id,
            },
        })),
    };
}

function updateMapSource(waypoints: wayPoint[]) {
    if (!map || !mapLoaded) return;
    const source = map.getSource("route") as maplibregl.GeoJSONSource | undefined;
    if (!source) return;

    source.setData(buildFeatureCollection(waypoints));

    const allCoords = waypoints.flatMap((wp) => [
        [wp.geo_start[0], wp.geo_start[1]] as [number, number],
        [wp.geo_end[0], wp.geo_end[1]] as [number, number],
    ]);
    if (allCoords.length > 0) {
        const bounds = allCoords.reduce(
            (b, coord) => b.extend(coord),
            new maplibregl.LngLatBounds(allCoords[0], allCoords[0]),
        );
        map.fitBounds(bounds, { padding: 60, maxZoom: 16 });
    }
}

function locateUser() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            const coords: [number, number] = [pos.coords.longitude, pos.coords.latitude];
            userLngLat.value = coords;

            if (userMarker) {
                userMarker.setLngLat(coords);
            } else {
                const el = document.createElement("div");
                el.className = "user-location-dot";
                userMarker = new maplibregl.Marker({ element: el, anchor: "center" })
                    .setLngLat(coords)
                    .addTo(map!);
            }

            map?.flyTo({ center: coords, zoom: 13, duration: 1500 });
        },
        (err) => {
            console.warn("Geolocation unavailable:", err.message);
        },
        { enableHighAccuracy: true, timeout: 10000 }
    );
}

function flyToUser() {
    if (!userLngLat.value || !map) return;
    map.flyTo({ center: userLngLat.value, zoom: 14, duration: 1000 });
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

        map!.addSource("route", {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
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

        map!.on("mousemove", "route", (e) => {
            if (!e.features || e.features.length === 0) return;
            map!.getCanvas().style.cursor = "pointer";

            const p = e.features[0].properties as Record<string, unknown>;
            const restriction = p.restriction_type
                ? `<br><span style="color:#aaa">Restriction:</span> ${p.restriction_type}`
                : "";
            const html = `
                <div style="font-size:12px;line-height:1.8;padding:2px 4px">
                    <strong>${p.name}</strong><br>
                    <span style="color:#aaa">Road type:</span> ${p.road_type} (tag&nbsp;${p.tag_id})<br>
                    <span style="color:#aaa">Seq:</span> ${p.seq}<br>
                    <span style="color:#aaa">Cost:</span> ${Number(p.cost).toFixed(8)}<br>
                    <span style="color:#aaa">OSM ID:</span> ${p.osm_id}<br>
                    <span style="color:#aaa">Edge ID:</span> ${p.edge_id}${restriction}
                </div>`;

            if (popup) popup.remove();
            popup = new maplibregl.Popup({ closeButton: false, offset: 8 })
                .setLngLat(e.lngLat)
                .setHTML(html)
                .addTo(map!);
        });

        map!.on("mouseleave", "route", () => {
            map!.getCanvas().style.cursor = "";
            if (popup) {
                popup.remove();
                popup = null;
            }
        });

        if (route.value.length > 0) {
            updateMapSource(toRaw(route.value));
        }

        locateUser();
    });
});

watch(route, (newRoute) => {
    updateMapSource(toRaw(newRoute));
});

// When parent passes new waypoints, update the map
watch(() => props.waypoints, (newWaypoints) => {
    if (newWaypoints && newWaypoints.length > 0) {
        route.value = newWaypoints;
    }
}, { deep: true });

async function onSubmitOSM() {
    if (osm_id_1.value === null || osm_id_2.value === null) {
        error.value = "Please enter both OSM IDs";
        return;
    }
    loading.value = true;
    error.value = null;
    try {
        route.value = await getRoute(osm_id_1.value, osm_id_2.value);
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

        <div class="map-outer">
            <div ref="mapContainer" class="map-container" />
            <button
                class="locate-btn"
                :class="{ 'locate-active': userLngLat }"
                :title="userLngLat ? 'Return to my location' : 'Waiting for location…'"
                @click="flyToUser"
            >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="8"/>
                    <line x1="12" y1="2" x2="12" y2="6"/>
                    <line x1="12" y1="18" x2="12" y2="22"/>
                    <line x1="2" y1="12" x2="6" y2="12"/>
                    <line x1="18" y1="12" x2="22" y2="12"/>
                    <circle cx="12" cy="12" r="3" fill="currentColor"/>
                </svg>
            </button>
        </div>
    </div>
</template>

<style scoped>
.map-wrapper {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
}

.map-controls {
    display: none;
}
.map-controls-hidden {
    display: flex;
    gap: 8px;
    align-items: center;
    padding: 8px;
    background: #1a1a2e;
    flex-shrink: 0;
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

.map-outer {
    flex: 1;
    position: relative;
    min-height: 0;
}

.map-container {
    position: absolute;
    inset: 0;
    width: 100%;
    height: 100%;
}

.locate-btn {
    position: absolute;
    right: 10px;
    bottom: 80px;
    z-index: 10;
    width: 36px;
    height: 36px;
    background: #ffffff;
    border: none;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    color: #9aa0a6;
    transition: background 0.15s, color 0.15s;
}
.locate-btn:hover {
    background: #f8f9fa;
    color: #5f6368;
}
.locate-btn.locate-active {
    color: #1a73e8;
}
.locate-btn.locate-active:hover {
    background: rgba(26, 115, 232, 0.08);
}
</style>
