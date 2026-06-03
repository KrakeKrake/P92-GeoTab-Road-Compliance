<script setup lang="ts">
import { onMounted, ref } from "vue";
import maplibregl from "maplibre-gl";

const mapContainer = ref<HTMLElement | null>(null);

onMounted(() => {
    const map = new maplibregl.Map({
        container: mapContainer.value!,
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
                    coordinates: [
                        [144.9631, -37.8136],
                        [144.97, -37.82],
                        [144.98, -37.83],
                    ],
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
    <div ref="mapContainer" style="height: 600px" />
</template>
