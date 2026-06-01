<template>
  <div class="map-area">
    <div ref="mapContainer" class="map-container"></div>

    <div v-if="!routeGeojson" class="map-empty">
      <div class="map-empty-icon">🗺️</div>
      <div class="map-empty-text">Enter origin and destination to plan a route</div>
    </div>

    <div class="map-attr">
      © <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors
    </div>
  </div>
</template>

<script>
import maplibregl from 'maplibre-gl'

export default {
  name: 'MapView',

  props: {
    routeGeojson: { type: Object, default: null },
    violations:   { type: Array,  default: () => [] },
  },

  data() {
    return { map: null }
  },

  mounted() {
    this.map = new maplibregl.Map({
      container: this.$refs.mapContainer,
      style:     'https://tiles.openfreemap.org/styles/liberty',
      center:    [144.9631, -37.8136],
      zoom:      11,
      attributionControl: false,
    })
    this.map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
    this.map.addControl(new maplibregl.ScaleControl({ unit: 'metric' }), 'bottom-right')
  },

  beforeUnmount() {
    this.map?.remove()
  },

  watch: {
    // When parent passes new route GeoJSON, draw it on the map
    routeGeojson(geojson) {
      if (!geojson) return
      this.map.once('idle', () => {
        if (this.map.getSource('route')) {
          this.map.getSource('route').setData(geojson)
        } else {
          this.map.addSource('route', { type: 'geojson', data: geojson })
          this.map.addLayer({ id: 'route-glow',   type: 'line', source: 'route', paint: { 'line-color': '#4285f4', 'line-width': 14, 'line-opacity': 0.18, 'line-blur': 4 }, layout: { 'line-cap': 'round', 'line-join': 'round' } })
          this.map.addLayer({ id: 'route-casing', type: 'line', source: 'route', paint: { 'line-color': '#1a6fd4', 'line-width': 9  }, layout: { 'line-cap': 'round', 'line-join': 'round' } })
          this.map.addLayer({ id: 'route-line',   type: 'line', source: 'route', paint: { 'line-color': '#4285f4', 'line-width': 6  }, layout: { 'line-cap': 'round', 'line-join': 'round' } })
        }
        // Fit map to route bounds
        const coords = geojson.geometry?.coordinates || []
        if (coords.length) {
          const bounds = coords.reduce(
            (b, c) => b.extend(c),
            new maplibregl.LngLatBounds(coords[0], coords[0])
          )
          this.map.fitBounds(bounds, { padding: 60, maxZoom: 14 })
        }
      })
    },

    // When violations come in, add markers on map
    violations(list) {
      list.forEach(v => {
        if (!v.coordinates) return
        const el = document.createElement('div')
        el.className = 'violation-map-marker'
        el.textContent = '⚠'
        new maplibregl.Marker({ element: el })
          .setLngLat(v.coordinates)
          .setPopup(new maplibregl.Popup({ offset: 20 }).setHTML(`<strong>${v.road_name}</strong><br>${v.detail}`))
          .addTo(this.map)
      })
    },
  },
}
</script>

<style scoped>
.map-container {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}
.violation-map-marker {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(217, 48, 37, 0.12);
  border: 2px solid #d93025;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  cursor: pointer;
  animation: vpulse 1.5s ease-in-out infinite;
}
@keyframes vpulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50%       { transform: scale(1.2); opacity: 0.7; }
}
</style>
