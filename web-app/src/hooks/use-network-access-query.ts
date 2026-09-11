import { useQuery } from '@tanstack/react-query';
import type {
  NetworkAccessMap,
  NetworkAccessType,
} from '@/components/map/types';
import { useCommonStore } from '@/stores/common-store';
import { useNetworkAccessStore } from '@/stores/nhvr-store';

const ACCESS_MAP: Record<number, NetworkAccessType> = {
  0: 'allowed',
  1: 'conditional',
  2: 'restricted',
};

const NHVR_API_URL =
  import.meta.env.VITE_NHVR_API_URL || 'http://localhost:5000';

async function fetchNetworkAccess(
  networks: string[]
): Promise<NetworkAccessMap> {
  const params = new URLSearchParams();
  networks.forEach((n) => params.append('network', n));
  const response = await fetch(
    `${NHVR_API_URL}/api/nhvr-access/query?${params}`
  );
  if (!response.ok) throw new Error('Could not fetch network access data');
  const raw = await response.json();
  const map: NetworkAccessMap = {};
  for (const [wayId, entries] of Object.entries(raw)) {
    map[wayId] = (entries as any[]).map((e) => ({
      networkName: e.networkName,
      access: ACCESS_MAP[e.access] ?? 'allowed',
      description: e.description ?? '',
      road_manager: e.manager ?? '',
    }));
  }
  return map;
}

export function useNetworkAccessQuery() {
  const nhvrNetworks = useCommonStore((s) => s.settings.nhvr_networks);
  const setNetworkAccess = useNetworkAccessStore((s) => s.setNetworkAccess);

  return useQuery({
    queryKey: ['network-access', nhvrNetworks],
    queryFn: async () => {
      if (!nhvrNetworks || nhvrNetworks.length === 0) {
        setNetworkAccess({});
        return {};
      }
      const data = await fetchNetworkAccess(nhvrNetworks);
      setNetworkAccess(data);
      return data;
    },
  });
}
