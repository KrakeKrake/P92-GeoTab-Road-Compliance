<script setup lang="ts">
import { onMounted, ref, toRaw } from "vue";
import maplibregl from "maplibre-gl";

const mapContainer = ref<HTMLElement | null>(null);
const props = defineProps<{
    route?: number[][];
}>();

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
                    coordinates: toRaw(props.route),
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
</script>

<template>
    <div ref="mapContainer" style="height: 600px; width: 100%" />
</template>

<style scoped></style>
