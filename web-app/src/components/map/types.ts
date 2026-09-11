import type { MAP_STYLES } from './constants';

export interface LastCenterStorageValue {
  center: [number, number];
  zoom_level: number;
}

// Add the types for the network access layer.
export type NetworkAccessType = 'restricted' | 'conditional' | 'allowed';
export interface NetworkAccessEntry {
  networkName: string;
  access: NetworkAccessType;
  description: string;
  road_manager: string;
}
export type NetworkAccessMap = Record<string, NetworkAccessEntry[]>;

export type BuiltInMapStyleId = (typeof MAP_STYLES)[number]['id'];
export type MapStyleType = BuiltInMapStyleId | 'custom';
