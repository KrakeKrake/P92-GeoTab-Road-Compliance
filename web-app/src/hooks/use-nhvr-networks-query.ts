import { useQuery } from '@tanstack/react-query';
import { NHVR_API_URL } from '@/utils/nhvr-api';

interface NetworksResponse {
  networks?: unknown;
}

/**
 * Fetch the network names that are actually present in the NHVR table.
 *
 * The API derives the list from nhvr_access.nhvr_network_access, so it changes
 * when ./update.sh reloads the GeoPackages and never drifts from the routes
 * /api/nhvr-access/query can return.
 */
export async function fetchNhvrNetworks(): Promise<string[]> {
  const response = await fetch(`${NHVR_API_URL}/api/nhvr-access/networks`);
  if (!response.ok) {
    throw new Error('Could not fetch NHVR networks');
  }

  const raw = (await response.json()) as NetworksResponse;
  if (!Array.isArray(raw.networks)) return [];

  return raw.networks.filter(
    (name): name is string => typeof name === 'string' && name.length > 0
  );
}

// Shown while the request is in flight. A stable reference keeps it safe to use
// in effect dependency arrays.
export const EMPTY_NETWORKS: string[] = [];

export function useNhvrNetworksQuery() {
  return useQuery({
    queryKey: ['nhvr-networks'],
    queryFn: fetchNhvrNetworks,
    // The list only changes when the data is reloaded.
    staleTime: 5 * 60 * 1000,
    select: (networks) => (networks.length > 0 ? networks : EMPTY_NETWORKS),
  });
}
