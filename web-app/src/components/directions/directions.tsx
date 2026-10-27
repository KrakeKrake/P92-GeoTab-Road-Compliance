import { useCallback, useEffect, useRef } from 'react';

import { Waypoints } from './waypoints/waypoint-list';

import { SettingsFooter } from '@/components/settings-footer';
import { QuickSettings } from '@/components/quick-settings';

import type { ParsedDirectionsGeometry } from '@/components/types';
import { Button } from '@/components/ui/button';
import { MapPinPlus, MapPinXInside } from 'lucide-react';
import { RouteCard } from './route-card';
import { parseUrlParams } from '@/utils/parse-url-params';
import { isValidCoordinates } from '@/utils/geom';
import { useNavigate, useSearch } from '@tanstack/react-router';
import { useDirectionsStore } from '@/stores/directions-store';
import {
  useDirectionsQuery,
  useSetWaypointFromCoords,
} from '@/hooks/use-directions-queries';
import { useOptimizedRouteQuery } from '@/hooks/use-optimized-route-query';
import { Sparkles } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { useCommonStore } from '@/stores/common-store';
import { MultiSelectSetting } from '@/components/ui/multiselect-setting';
import {
  EMPTY_NETWORKS,
  useNhvrNetworksQuery,
} from '@/hooks/use-nhvr-networks-query';
import { NHVR_NETWORK_LABELS } from '@/utils/nhvr-network-labels';
import { useComplianceStore } from '@/stores/compliance-store';
const VEHICLE_TO_NHVR_NETWORK: Record<string, string> = {
  B_DOUBLE: 'B_DOUBLE',
  TYPE_1_ROAD_TRAIN: 'Vic Road Train Gazetted (Ref 1)',
  TYPE_2_ROAD_TRAIN: 'Vic Road Train Gazetted (Ref 1)',
};

const COMPLIANCE_TO_NHVR_NETWORK: Record<string, string> = {
  GHMS_B_DOUBLE: 'GHMS_B_DOUBLE',
  GHMS_RIGID_SEMI: 'GHMS_SEMI_TRAILERS',
  ROAD_TRAIN_HAY_GRAIN: 'Vic Road Train Hay & Grain Pre-Approved (Ref 2)',
  EMERGENCY_DROUGHT_NETWORK: '28361546',
};

export const DirectionsControl = () => {
  const waypoints = useDirectionsStore((state) => state.waypoints);
  const results = useDirectionsStore((state) => state.results);
  const addEmptyWaypointToEnd = useDirectionsStore(
    (state) => state.addEmptyWaypointToEnd
  );
  const clearWaypoints = useDirectionsStore((state) => state.clearWaypoints);
  const clearRoutes = useDirectionsStore((state) => state.clearRoutes);
  const initialUrlParams = useRef(parseUrlParams());
  const urlParamsProcessed = useRef(false);
  const navigate = useNavigate({ from: '/$activeTab' });
  const { refetch: refetchDirections } = useDirectionsQuery();
  const { setWaypointFromCoords } = useSetWaypointFromCoords();
  const { optimizeRoute, isPending: isOptimizing } = useOptimizedRouteQuery();
  const isOptimized = useDirectionsStore((state) => state.isOptimized);
  const activeRouteIndex = useDirectionsStore(
    (state) => state.activeRouteIndex
  );
  const setActiveRouteIndex = useDirectionsStore(
    (state) => state.setActiveRouteIndex
  );
  const { profile } = useSearch({ from: '/$activeTab' });
  const settings = useCommonStore((state) => state.settings);
  const updateSettings = useCommonStore((state) => state.updateSettings);
  const routingPreset = useComplianceStore((state) => state.routingPreset);
  const appliedVehicle = useComplianceStore(
    (state) => state.appliedVehicle
  );
  const { data: nhvrNetworkOptions = EMPTY_NETWORKS } = useNhvrNetworksQuery();
  const lastAppliedNetwork = useRef<string | null>(null);
useEffect(() => {
  if (profile !== 'truck') return;

  const overrideKey = routingPreset?.networkOverrideKey;

  // Goods-specific network takes priority
  const overrideNetwork = overrideKey
    ? COMPLIANCE_TO_NHVR_NETWORK[overrideKey]
    : undefined;

  // Otherwise use the vehicle's normal network
  const baseNetwork = appliedVehicle?.templateId
    ? VEHICLE_TO_NHVR_NETWORK[appliedVehicle.templateId]
    : undefined;

  const networkName = overrideNetwork ?? baseNetwork;

  // Recommendations only make sense if the server actually has that network.
  // The list is loaded asynchronously, so this effect re-runs when it arrives.
  if (!networkName || !nhvrNetworkOptions.includes(networkName)) return;

  // Do not repeatedly apply the same recommendation
  if (lastAppliedNetwork.current === networkName) {
    return;
  }

  lastAppliedNetwork.current = networkName;

  // Automatically preselect the recommended network
  updateSettings('nhvr_networks', [networkName]);

  refetchDirections();

}, [
  routingPreset?.networkOverrideKey,
  appliedVehicle?.templateId,
  profile,
  nhvrNetworkOptions,
  updateSettings,
  refetchDirections,
]);

// Drop selections that are no longer present in the server's network table,
// e.g. after a data update removed or renamed a network.
useEffect(() => {
  if (nhvrNetworkOptions.length === 0) return;
  const selected = settings.nhvr_networks;
  const valid = selected.filter((name) => nhvrNetworkOptions.includes(name));
  if (valid.length !== selected.length) {
    updateSettings('nhvr_networks', valid);
    refetchDirections();
  }
}, [
  nhvrNetworkOptions,
  settings.nhvr_networks,
  updateSettings,
  refetchDirections,
]);
  useEffect(() => {
  if (profile !== 'truck') return;

  const carryingDangerousGoods =
    routingPreset?.goodsTypeId === 'DANGEROUS_GOODS';

  if (settings.hazmat === carryingDangerousGoods) {
    return;
  }

  updateSettings(
    'hazmat',
    carryingDangerousGoods
  );

  refetchDirections();
}, [
  routingPreset?.goodsTypeId,
  profile,
  settings.hazmat,
  updateSettings,
  refetchDirections,
]);
  useEffect(() => {
    if (urlParamsProcessed.current) return;

    const alreadyHydrated = useDirectionsStore
      .getState()
      .waypoints.some((wp) => wp.geocodeResults.some((r) => r.selected));
    if (alreadyHydrated) {
      urlParamsProcessed.current = true;
      return;
    }

    const wpsParam = initialUrlParams.current.wps;

    if (wpsParam) {
      const coordinates = wpsParam.split(',').map(Number);

      for (let i = 0; i < coordinates.length; i += 2) {
        const lng = coordinates[i]!;
        const lat = coordinates[i + 1]!;

        if (!isValidCoordinates(lat, lng) || isNaN(lng) || isNaN(lat)) continue;

        const index = i / 2;
        setWaypointFromCoords(lng, lat, index, { isPermalink: true });
      }
      refetchDirections();
    }

    urlParamsProcessed.current = true;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const wps: number[] = [];

    for (const wp of waypoints) {
      for (const result of wp.geocodeResults) {
        if (result.selected && result.sourcelnglat) {
          wps.push(result.sourcelnglat[0], result.sourcelnglat[1]);
        }
      }
    }

    navigate({
      search: (prev) => ({
        ...prev,
        wps: wps.length > 0 ? wps.join(',') : undefined,
      }),
      replace: true,
    });
  }, [waypoints, navigate]);

  const handleAddWaypoint = useCallback(() => {
    addEmptyWaypointToEnd();
  }, [addEmptyWaypointToEnd]);

  const handleRemoveWaypoints = useCallback(() => {
    clearWaypoints();
    clearRoutes();
  }, [clearWaypoints, clearRoutes]);

  const activeWaypointsCount = waypoints.filter((wp) =>
    wp.geocodeResults.some((r) => r.selected)
  ).length;

  return (
    <>
      <div className="flex flex-col gap-3">
        <Waypoints />
        {profile === 'truck' && (
          <MultiSelectSetting
            id="nhvr_networks"
            label="NHVR Networks"
            description="The NHVR network to use for routing"
            value={settings.nhvr_networks}
            options={nhvrNetworkOptions}
            optionLabels={NHVR_NETWORK_LABELS}
            onValueChange={(value) => {
              updateSettings('nhvr_networks', value);
              refetchDirections();
            }}
          />
        )}

        <div className="flex justify-between gap-4">
          <Button
            variant="outline"
            onClick={handleAddWaypoint}
            data-testid="add-waypoint-button"
            className="w-full shrink"
          >
            <MapPinPlus className="size-5" />
            Add Waypoint
          </Button>
          <Button
            variant="destructive-outline"
            onClick={handleRemoveWaypoints}
            data-testid="reset-waypoints-button"
            className="w-full shrink"
            disabled={
              waypoints.length < 3 && waypoints.every((wp) => !wp.userInput)
            }
          >
            <MapPinXInside className="size-5" />
            Reset Waypoints
          </Button>
        </div>
        <Tooltip open={activeWaypointsCount >= 4 ? false : undefined}>
          <TooltipTrigger asChild>
            <span>
              <Button
                variant="outline"
                onClick={() => optimizeRoute()}
                disabled={
                  activeWaypointsCount < 4 || isOptimizing || isOptimized
                }
                className="w-full"
              >
                <Sparkles className="size-4" />
                Optimize Route
              </Button>
            </span>
          </TooltipTrigger>
          <TooltipContent>
            <p>You should have at least 4 waypoints to optimize the route</p>
          </TooltipContent>
        </Tooltip>
      </div>
      <QuickSettings />
      <SettingsFooter />
      {results.data && (
        <div>
          <h3 className="font-bold mb-2">Directions</h3>
          <div className="flex flex-col gap-3">
            <RouteCard
              data={results.data}
              index={0}
              isActive={activeRouteIndex === 0}
              onSelect={() => setActiveRouteIndex(0)}
            />
            {results.data.alternates?.map((alternate, index) => (
              <RouteCard
                data={alternate as ParsedDirectionsGeometry}
                key={alternate.id}
                index={index + 1}
                isActive={activeRouteIndex === index + 1}
                onSelect={() => setActiveRouteIndex(index + 1)}
              />
            ))}
          </div>
        </div>
      )}
    </>
  );
};
