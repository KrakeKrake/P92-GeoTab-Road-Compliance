<script setup lang="ts">
import { onMounted, ref, toRaw, watch } from "vue";
import maplibregl from "maplibre-gl";
import { getRoute } from "../../scripts/api.ts";
import type { wayPoint } from "../../scripts/api.ts";

const mapContainer = ref<HTMLElement | null>(null);
const route = ref<wayPoint[]>([]);
const osm_id_1 = ref<number | null>(null);
const osm_id_2 = ref<number | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

let map: maplibregl.Map | null = null;
let mapLoaded = false;
let popup: maplibregl.Popup | null = null;

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
    const source = map.getSource("route") as
        | maplibregl.GeoJSONSource
        | undefined;
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
    });
});

watch(route, (newRoute) => {
    updateMapSource(toRaw(newRoute));
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
