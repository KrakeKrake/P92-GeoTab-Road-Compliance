import { useMemo } from 'react';
import { Source, Layer } from 'react-map-gl/maplibre';
import { useNetworkAccessStore } from '@/stores/nhvr-store';
import { getValhallaTileUrl } from '@/components/tiles/valhalla-layers';
import { useNetworkAccessQuery } from '@/hooks/use-network-access-query';

export const NETWORK_ACCESS_SOURCE_ID = 'network-access-source';
export const NETWORK_ACCESS_LAYER_ID = 'network-access-layer';
export const NETWORK_ACCESS_HIT_TARGET_LAYER_ID = 'network-access-hit-target';

export function NetworkAccessLayer() {
  useNetworkAccessQuery();
  const networks = useNetworkAccessStore((state) => state.networks);
  const { restrictedIds, conditionalIds } = useMemo(() => {
    const restricted: string[] = [];
    const conditional: string[] = [];
    for (const [wayId, entries] of Object.entries(networks)) {
      if (entries.some((e) => e.access === 'restricted'))
        restricted.push(wayId);
      if (entries.some((e) => e.access === 'conditional'))
        conditional.push(wayId);
    }
    return { restrictedIds: restricted, conditionalIds: conditional };
  }, [networks]);

  return (
    <Source
      id={NETWORK_ACCESS_SOURCE_ID}
      type="vector"
      tiles={[getValhallaTileUrl()]}
      minzoom={7}
      maxzoom={14}
      scheme="xyz"
    >
      <Layer
        id={NETWORK_ACCESS_LAYER_ID}
        type="line"
        source-layer="edges"
        paint={{
          'line-color': [
            'case',
            [
              'in',
              ['to-string', ['get', 'osm_id']],
              ['literal', restrictedIds],
            ],
            '#ff0000',
            [
              'in',
              ['to-string', ['get', 'osm_id']],
              ['literal', conditionalIds],
            ],
            '#ffef2d',
            'rgba(0,0,0,0)',
          ],
          'line-width': 12,
          'line-opacity': 0.9,
        }}
      />
      {/* transparent wide line for easier clicking/hovering */}
      <Layer
        id={NETWORK_ACCESS_HIT_TARGET_LAYER_ID}
        type="line"
        source-layer="edges"
        paint={{ 'line-color': '#000', 'line-width': 12, 'line-opacity': 0 }}
      />
    </Source>
  );
}
