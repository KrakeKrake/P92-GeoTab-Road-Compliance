import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { NetworkAccessMap } from '@/components/map/types';
import { placeholderNetworkAccess } from '@/utils/network-access-placeholder';

interface NetworkAccessState {
  networks: NetworkAccessMap;
  setNetworkAccess: (networks: NetworkAccessMap) => void;
}

export const useNetworkAccessStore = create<NetworkAccessState>()(
  devtools(
    immer((set) => ({
      networks: placeholderNetworkAccess,
      setNetworkAccess: (networks) => set({ networks }),
    })),
    { name: 'network-access' }
  )
);
