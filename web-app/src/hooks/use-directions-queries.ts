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

  // Map clicks (and some geocoder results) can be off-road. Give Loki enough
  // room to snap to a truck-accessible edge; without it the truck profile
  // returns "No path could be found" for otherwise routable points.
  valhallaRequest.json.locations = valhallaRequest.json.locations.map(
    (location) => ({ ...location, radius: 50 })
  );

  const params = new URLSearchParams({
    json: JSON.stringify(valhallaRequest.json),
  });

  const response = await fetch(`${getValhallaUrl()}/route?${params}`, {
    headers: {
      'Content-Type': 'application/json',
      ...VALHALLA_CLIENT_HEADERS,
    },
  });

  let routeResponse = response;

  if (!routeResponse.ok) {
    const errorData = await routeResponse.json().catch(() => ({}));
    // A selected NHVR network can make the route impossible (for example a
    // bus-only network on a truck route). Retry without the network filter so
    // the user still gets a route and can see the network markings.
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const requestJson = valhallaRequest.json as any;
    const selectedNetworks =
      requestJson.costing_options?.[requestJson.costing]?.nhvr_networks;

    if (
      errorData.error_code === 442 &&
      Array.isArray(selectedNetworks) &&
      selectedNetworks.length > 0
    ) {
      const fallbackJson = JSON.parse(JSON.stringify(requestJson));
      if (fallbackJson.costing_options?.[fallbackJson.costing]) {
        delete fallbackJson.costing_options[fallbackJson.costing].nhvr_networks;
      }
      delete fallbackJson.filters;

      const fallbackParams = new URLSearchParams({
        json: JSON.stringify(fallbackJson),
      });
      const fallbackResponse = await fetch(
        `${getValhallaUrl()}/route?${fallbackParams}`,
        {
          headers: {
            'Content-Type': 'application/json',
            ...VALHALLA_CLIENT_HEADERS,
          },
        }
      );

      if (fallbackResponse.ok) {
        toast.warning('No route with the selected NHVR network', {
          description:
            'Showing a route without the network restriction. Clear the selection or choose another network.',
          position: 'bottom-center',
          duration: 7000,
          closeButton: true,
        });
        routeResponse = fallbackResponse;
      } else {
        let error_msg = errorData.error || 'Could not fetch resource';
        if (errorData.error_code === 154) {
          error_msg += ` for route.`;
        }
        throw new Error(error_msg);
      }
    } else {
      let error_msg = errorData.error || 'Could not fetch resource';
      if (errorData.error_code === 154) {
        error_msg += ` for route.`;
      }
      throw new Error(error_msg);
    }
  }

  const data: ValhallaRouteResponse = await routeResponse.json();

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
