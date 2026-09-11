import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import type { NetworkAccessMap } from '@/components/map/types';

interface NetworkAccessState {
  networks: NetworkAccessMap;
  setNetworkAccess: (networks: NetworkAccessMap) => void;
}

export const useNetworkAccessStore = create<NetworkAccessState>()(
  devtools(
    immer((set) => ({
      networks: {  },
      setNetworkAccess: (networks) => set({ networks }),
    })),
    { name: 'network-access' }
  )
);
