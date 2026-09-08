import type { NetworkAccessMap } from '@/components/map/types';

export const placeholderNetworkAccess: NetworkAccessMap = {
  '389828675': [
    {
      networkName: 'NHVR',
      access: 'restricted',
      description: 'No B-double access',
      road_manager: 'Something council',
    },
    {
      networkName: 'Council',
      access: 'conditional',
      description: 'Allowed only between 9 to 5',
      road_manager: 'Something council',
    },
  ],
};
