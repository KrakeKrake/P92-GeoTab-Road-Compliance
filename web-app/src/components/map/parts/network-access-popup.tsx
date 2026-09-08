import { Popup } from 'react-map-gl/maplibre';
import { Badge } from '@/components/ui/badge';
import { useNetworkAccessStore } from '@/stores/nhvr-store';

interface Props {
  lng: number;
  lat: number;
  wayId: string;
  onClose: () => void;
}
export function NetworkAccessPopup({ lng, lat, wayId, onClose }: Props) {
  const networks = useNetworkAccessStore((s) => s.networks);
  const entries = networks[wayId] ?? [];
  return (
    <Popup
      longitude={lng}
      latitude={lat}
      anchor="bottom"
      closeOnClick={false}
      onClose={onClose}
      closeButton={false}
      maxWidth="none"
    >
      <div className="max-w-sm p-2">
        <div className="font-bold">OSM way {wayId}</div>
        {entries.map((e) => (
          <div key={e.networkName} className="border-b py-1">
            <span className="font-semibold">{e.networkName}</span>
            <Badge
              variant={e.access === 'restricted' ? 'destructive' : 'outline'}
            >
              {e.access}
            </Badge>
            <p className="text-xs text-muted-foreground">{e.description}</p>
            <p className="text-xs text-muted-foreground">{e.road_manager}</p>
          </div>
        ))}
      </div>
    </Popup>
  );
}
