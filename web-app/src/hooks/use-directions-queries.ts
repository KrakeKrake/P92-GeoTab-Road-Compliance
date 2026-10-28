import { useQuery } from '@tanstack/react-query';
import { toast } from 'sonner';

import type {
  ActiveWaypoint,
  ParsedDirectionsGeometry,
  ValhallaRouteResponse,
} from '@/components/types';
import {
  getValhallaUrl,
  buildDirectionsRequest,
  parseDirectionsGeometry,
  showValhallaWarnings,
  VALHALLA_CLIENT_HEADERS,
} from '@/utils/valhalla';
import { forward_geocode, parseGeocodeResponse } from '@/utils/nominatim';
import { filterProfileSettings } from '@/utils/filter-profile-settings';
import { getDirectionsLanguage } from '@/utils/directions-language';
import { useCommonStore } from '@/stores/common-store';
import { useDirectionsStore, type Waypoint } from '@/stores/directions-store';
import { router } from '@/routes';

const getActiveWaypoints = (waypoints: Waypoint[]): ActiveWaypoint[] =>
  waypoints.flatMap((wp) => wp.geocodeResults.filter((r) => r.selected));

/**
 * Return the first network that this route is known to traverse on a
 * prohibited edge, or null when it is legal for all selected networks.
 */
function blockedNetworkForRoute(
  route: ValhallaRouteResponse,
  selectedNetworks: string[]
): string | null {
  for (const leg of route.trip.legs ?? []) {
    for (const maneuver of leg.maneuvers ?? []) {
      const blocked = maneuver.nhvr_networks?.find(
        (network) =>
          network.status === 'prohibited' &&
          selectedNetworks.includes(network.name)
      );
      if (blocked) return blocked.name;
    }
  }
  return null;
}

async function fetchDirections() {
  const waypoints = useDirectionsStore.getState().waypoints;
  const profile = router.state.location.search.profile;
  const { dateTime, settings: rawSettings } = useCommonStore.getState();

  const activeWaypoints = getActiveWaypoints(waypoints);
  if (activeWaypoints.length < 2) {
    return null;
  }

  const settings = filterProfileSettings(profile || 'bicycle', rawSettings);
  const language = getDirectionsLanguage();

  const valhallaRequest = buildDirectionsRequest({
    profile: profile || 'bicycle',
    activeWaypoints,
    // @ts-expect-error todo: initial settings and filtered settings types mismatch
    settings,
    dateTime,
    language,
  });

  // Map clicks (and some geocoder results) can be off-road. Loki snaps each
  // location to the nearest legal truck edge within this radius. 50 m was too
  // tight when a destination sits next to a restricted road: the nearest legal
  // edge can be just over 50 m away, making a legal detour look unreachable.
  // Start at 100 m and retry with a larger radius if Valhalla finds no path.
  const buildRouteUrl = (radius: number) => {
    const json = {
      ...valhallaRequest.json,
      locations: valhallaRequest.json.locations.map((location) => ({
        ...location,
        radius,
      })),
    };
    return `${getValhallaUrl()}/route?${new URLSearchParams({
      json: JSON.stringify(json),
    })}`;
  };

  const requestRoute = (radius: number) =>
    fetch(buildRouteUrl(radius), {
      headers: {
        'Content-Type': 'application/json',
        ...VALHALLA_CLIENT_HEADERS,
      },
    });

  let routeResponse = await requestRoute(100);
  if (!routeResponse.ok) {
    let errorData = await routeResponse
      .clone()
      .json()
      .catch(() => ({}));
    if (errorData.error_code === 442) {
      for (const radius of [250, 500]) {
        const retry = await requestRoute(radius);
        routeResponse = retry;
        if (retry.ok) break;
        errorData = await retry
          .clone()
          .json()
          .catch(() => ({}));
        if (errorData.error_code !== 442) break;
      }
    }
  }
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const requestJson = valhallaRequest.json as any;
  const selectedNetworks =
    requestJson.costing_options?.[requestJson.costing]?.nhvr_networks;

  if (!routeResponse.ok) {
    const errorData = await routeResponse.json().catch(() => ({}));

    // A selected network is a hard constraint: restricted sections for that
    // network must never be used. Do not retry without the network filter -
    // that would silently route over the red (prohibited) sections.
    if (
      errorData.error_code === 442 &&
      Array.isArray(selectedNetworks) &&
      selectedNetworks.length > 0
    ) {
      throw new Error(
        `No route avoids the restricted sections of the selected NHVR network (${selectedNetworks.join(
          ', '
        )}). Change the network selection or the waypoints.`
      );
    }

    let error_msg = errorData.error || 'Could not fetch resource';
    if (errorData.error_code === 154) {
      error_msg += ` for route.`;
    }
    throw new Error(error_msg);
  }

  const data: ValhallaRouteResponse = await routeResponse.json();

  // Defence in depth: if Valhalla returns an illegal main route, prefer a
  // legal alternative instead of discarding the whole response. This also
  // covers hierarchy shortcuts that were built before the tile-builder guard.
  if (Array.isArray(selectedNetworks) && selectedNetworks.length > 0) {
    const blocked = blockedNetworkForRoute(data, selectedNetworks);
    const legalAlternates = (data.alternates ?? []).filter(
      (alternate): alternate is ValhallaRouteResponse =>
        Boolean(alternate) &&
        blockedNetworkForRoute(alternate, selectedNetworks) === null
    );

    if (blocked) {
      if (legalAlternates.length === 0) {
        throw new Error(
          `No route avoids the restricted sections of the selected NHVR network (${selectedNetworks.join(
            ', '
          )}). Change the network selection or the waypoints.`
        );
      }

      // Promote the first (best) legal alternate to the main route.
      const legal = legalAlternates[0] as ValhallaRouteResponse;
      const rest = legalAlternates.slice(1);
      data.trip = legal.trip;
      data.alternates = rest.length > 0 ? rest : undefined;

      toast.warning('Showing an alternative route', {
        description: `The fastest route crossed a section prohibited for ${blocked}. Showing a route that avoids it.`,
        position: 'bottom-center',
        duration: 7000,
        closeButton: true,
      });
    } else {
      // Drop any illegal alternates so they cannot be selected from the list.
      data.alternates =
        legalAlternates.length > 0 ? legalAlternates : undefined;
    }
  }

  // Parse geometry for main route
  (data as ParsedDirectionsGeometry).decodedGeometry =
    parseDirectionsGeometry(data);

  // Parse geometry for alternates
  data.alternates?.forEach((alternate, i) => {
    if (alternate) {
      (data.alternates![i] as ParsedDirectionsGeometry).decodedGeometry =
        parseDirectionsGeometry(alternate);
    }
  });

  showValhallaWarnings(data.trip.warnings);

  return data as ParsedDirectionsGeometry;
}

export function useDirectionsQuery() {
  const showLoading = useCommonStore((state) => state.showLoading);
  const zoomTo = useCommonStore((state) => state.zoomTo);
  const receiveRouteResults = useDirectionsStore(
    (state) => state.receiveRouteResults
  );
  const clearRoutes = useDirectionsStore((state) => state.clearRoutes);

  return useQuery({
    queryKey: ['directions'],
    queryFn: async () => {
      showLoading(true);
      try {
        const data = await fetchDirections();
        if (data) {
          receiveRouteResults({ data });
          zoomTo(data.decodedGeometry);
        }
        return data;
      } catch (error) {
        clearRoutes();
        if (error instanceof Error) {
          toast.warning('Error', {
            description: error.message,
            position: 'bottom-center',
            duration: 5000,
            closeButton: true,
          });
        }
        throw error;
      } finally {
        setTimeout(() => showLoading(false), 500);
      }
    },
    enabled: false,
    retry: false,
  });
}

export function useSetWaypointFromCoords() {
  const receiveGeocodeResults = useDirectionsStore(
    (state) => state.receiveGeocodeResults
  );
  const updateTextInput = useDirectionsStore((state) => state.updateTextInput);
  const addEmptyWaypointToEnd = useDirectionsStore(
    (state) => state.addEmptyWaypointToEnd
  );
  const updatePlaceholderAddressAtIndex = useDirectionsStore(
    (state) => state.updatePlaceholderAddressAtIndex
  );

  const setWaypointFromCoords = async (
    lng: number,
    lat: number,
    index: number,
    options?: { isPermalink?: boolean }
  ) => {
    // For permalink loading, add waypoint if needed
    if (options?.isPermalink) {
      const waypointCount = useDirectionsStore.getState().waypoints.length;
      const missingWaypoints = index + 1 - waypointCount;

      for (let i = 0; i < missingWaypoints; i++) {
        addEmptyWaypointToEnd();
      }
    }

    // Set placeholder immediately
    updatePlaceholderAddressAtIndex(index, lng, lat);

    const lngLat: [number, number] = [lng, lat];
    const address: ActiveWaypoint = {
      title: `${lng.toFixed(6)}, ${lat.toFixed(6)}`,
      key: 0,
      selected: true,
      addresslnglat: lngLat,
      sourcelnglat: lngLat,
      displaylnglat: lngLat,
      addressindex: 0,
    };
    const addresses = [address];
    receiveGeocodeResults({ addresses, index });
    updateTextInput({
      inputValue: address.title,
      index,
      addressindex: 0,
    });
    return addresses;
  };

  return { setWaypointFromCoords };
}

async function fetchForwardGeocode(
  userInput: string,
  lngLat?: [number, number]
): Promise<ActiveWaypoint[]> {
  if (lngLat) {
    return [
      {
        title: lngLat.toString(),
        key: 0,
        selected: false,
        addresslnglat: lngLat,
        sourcelnglat: lngLat,
        displaylnglat: lngLat,
        addressindex: 0,
      },
    ];
  }

  const response = await forward_geocode(userInput);
  const addresses = parseGeocodeResponse(response.data);

  if (addresses.length === 0) {
    toast.warning('No addresses', {
      description: 'Sorry, no addresses can be found.',
      position: 'bottom-center',
      duration: 5000,
      closeButton: true,
    });
  }

  return addresses as ActiveWaypoint[];
}

export function useForwardGeocodeDirections() {
  const receiveGeocodeResults = useDirectionsStore(
    (state) => state.receiveGeocodeResults
  );

  const forwardGeocode = async (
    userInput: string,
    index: number,
    lngLat?: [number, number]
  ) => {
    try {
      const addresses = await fetchForwardGeocode(userInput, lngLat);
      receiveGeocodeResults({
        addresses,
        index,
      });
      return addresses;
    } catch (error) {
      console.error('Forward geocode error:', error);
      throw error;
    }
  };

  return { forwardGeocode };
}
