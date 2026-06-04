<script setup lang="ts">
import { onMounted, ref, toRaw, computed, watch } from "vue";
import maplibregl from "maplibre-gl";
import { getRoute, get_geo } from "../../scripts/api.ts";
import type { Route, wayPoint } from "../../scripts/api.ts";

const mapContainer = ref<HTMLElement | null>(null);
// const props = defineProps<{
//     route?: Route;
// }>();
const route = ref<Route>();


onMounted(() => {
    const map = new maplibregl.Map({
        container: mapContainer.value,
        style: "https://tiles.openfreemap.org/styles/liberty",
        center: [144.9631, -37.8136],
        zoom: 10,
    });
    map.on("load", () => {
        map.addSource("route", {
            type: "geojson",
            data: {
                type: "Feature",
                geometry: {
                    type: "LineString",
                    coordinates: toRaw(geos.value),
                },
                properties: {},
            },
        });

        map.addLayer({
            id: "route",
            type: "line",
            source: "route",
            paint: {
                "line-color": "#ff0000",
                "line-width": 4,
            },
        });
    });
});

const osm_id_1 = ref<number>(0);
const osm_id_2 = ref<number>(0);
const geos = ref<number[][]>([]);
async function onSubmitOSM() {
  route.value = await getRoute(osm_id_1.value, osm_id_2.value);
  geos.value = await get_geo(route.value);
}

</script>

<template>
    <div>
        <input v-model="osm_id_1"></input>
        <input v-model="osm_id_2"></input>
        <button @click="onSubmitOSM">Submit</button>
    </div>
    <div ref="mapContainer" style="height: 600px; width: 100%" />
</template>

<style scoped></style>
