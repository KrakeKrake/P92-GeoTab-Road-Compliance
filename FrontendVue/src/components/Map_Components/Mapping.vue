<script setup>
import { LMap, LTileLayer, LPolyline } from "@vue-leaflet/vue-leaflet";

const zoom = 10;

const center = [-37.8136, 144.9631];

const linePoints = [
    [-37.8136, 144.9631],
    [-37.82, 144.97],
    [-37.83, 144.98],
];
</script>

<template>
    <p>Test</p>

    <l-map v-model:zoom="zoom" :center="center" style="height: 600px">
        <l-tile-layer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="© OpenStreetMap contributors"
        />

        <l-polyline :lat-lngs="linePoints" color="red" :weight="3" />
    </l-map>
</template>
