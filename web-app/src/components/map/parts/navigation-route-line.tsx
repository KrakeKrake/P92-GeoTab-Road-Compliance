import { Source, Layer } from 'react-map-gl/maplibre';
import { useNavigationStore } from '@/stores/navigation-store';

export const NavigationRouteLine = () => {
  const isNavigating = useNavigationStore((s) => s.isNavigating);
  const geometry = useNavigationStore((s) => s.geometry);

  if (!isNavigating || !geometry || geometry.length < 2) return null;

  // Store geometry is [lat, lng]; GeoJSON needs [lng, lat]
  const geojson: GeoJSON.Feature<GeoJSON.LineString> = {
    type: 'Feature',
    properties: {},
    geometry: {
      type: 'LineString',
      coordinates: geometry.map((pt) => [pt[1]!, pt[0]!]),
    },
  };

  return (
    <Source id="nav-route" type="geojson" data={geojson}>
      {/* White outline for contrast */}
      <Layer
        id="nav-route-outline"
        type="line"
        layout={{ 'line-cap': 'round', 'line-join': 'round' }}
        paint={{ 'line-color': '#ffffff', 'line-width': 9, 'line-opacity': 0.9 }}
      />
      {/* Blue route line */}
      <Layer
        id="nav-route-line"
        type="line"
        layout={{ 'line-cap': 'round', 'line-join': 'round' }}
        paint={{ 'line-color': '#3b82f6', 'line-width': 6, 'line-opacity': 1 }}
      />
    </Source>
  );
};
