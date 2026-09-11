import { Marker } from 'react-map-gl/maplibre';
import { Navigation } from 'lucide-react';
import { useNavigationStore } from '@/stores/navigation-store';

export const UserPositionMarker = () => {
  const isNavigating = useNavigationStore((state) => state.isNavigating);
  const currentPosition = useNavigationStore((state) => state.currentPosition);

  if (!isNavigating || !currentPosition) return null;

  return (
    <Marker
      latitude={currentPosition[0]}
      longitude={currentPosition[1]}
      anchor="center"
    >
      {/* No CSS rotation — the map bearing tracks heading, so the arrow always points up */}
      <div className="relative flex items-center justify-center">
        <div className="absolute size-14 rounded-full bg-blue-500/20 animate-pulse" />
        <div className="size-7 rounded-full bg-blue-600 border-2 border-white shadow-lg flex items-center justify-center">
          <Navigation size={14} className="text-white fill-white" />
        </div>
      </div>
    </Marker>
  );
};
