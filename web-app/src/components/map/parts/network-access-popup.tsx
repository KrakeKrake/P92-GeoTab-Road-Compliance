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
  const ACCESS_BADGE_STYLES = {
    restricted: { variant: 'destructive' as const, className: '' },
    conditional: {
      variant: 'outline' as const,
      className:
        'border-amber-500 bg-amber-500/10 text-amber-600 dark:text-amber-400',
    },
    allowed: {
      variant: 'outline' as const,
      className:
        'border-emerald-500 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
    },
  };
  const networks = useNetworkAccessStore((s) => s.networks);
  const entries = networks[wayId] ?? []; // Filter out "allowed" networks.
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
        {entries.map((e) => {
          const style =
            ACCESS_BADGE_STYLES[e.access] ?? ACCESS_BADGE_STYLES.allowed;
          return (
            <div key={e.networkName} className="border-b py-1">
              <span className="font-semibold">{e.networkName}</span>
              <Badge variant={style.variant} className={style.className}>
                {e.access}
              </Badge>
              <p className="text-xs text-muted-foreground">{e.description}</p>
              <p className="text-xs text-muted-foreground">{e.road_manager}</p>
            </div>
          );
        })}
      </div>
    </Popup>
  );
}
