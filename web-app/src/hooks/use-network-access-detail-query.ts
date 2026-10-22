import { useQuery } from '@tanstack/react-query';
import { getAppConfig } from '@/utils/runtime-config';

export interface NetworkAccessDetail {
  networkName: string;
  description: string;
  manager: string;
}

export type NetworkAccessDetailMap = Record<string, NetworkAccessDetail[]>;

const NHVR_API_URL = (
  getAppConfig().VITE_NHVR_API_URL ?? 'http://localhost:5000'
).replace(/\/$/, '');

async function fetchNetworkAccessByIds(
  wayIds: number[]
): Promise<NetworkAccessDetailMap> {
  const params = new URLSearchParams();
  wayIds.forEach((id) => params.append('ids', String(id)));

  const response = await fetch(
    `${NHVR_API_URL}/api/nhvr-access/query_id?${params}`
  );
  if (!response.ok) throw new Error('Could not fetch network access detail');

  const raw = await response.json();
  const map: NetworkAccessDetailMap = {};
  for (const [wayId, entries] of Object.entries(raw)) {
    map[wayId] = (
      entries as Array<{
        networkName: string;
        description: string | null;
        manager: string | null;
      }>
    ).map((entry) => ({
      networkName: entry.networkName,
      description: entry.description ?? '',
      manager: entry.manager ?? '',
    }));
  }
  return map;
}

export function useNetworkAccessDetailQuery(wayIds: number[]) {
  const deduped = [...new Set(wayIds)].sort((a, b) => a - b);

  return useQuery({
    queryKey: ['network-access-detail', deduped],
    queryFn: () => fetchNetworkAccessByIds(deduped),
    enabled: deduped.length > 0,
  });
}
