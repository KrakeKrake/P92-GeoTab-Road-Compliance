import { useEffect, useRef, useMemo } from 'react';
import { useNavigationStore } from '@/stores/navigation-store';
import type { Trip, Maneuver } from '@/components/types';

export interface FlatManeuver {
  maneuver: Maneuver;
  legIndex: number;
  globalBeginShapeIndex: number;
  globalEndShapeIndex: number;
}

function flattenManeuvers(trip: Trip): FlatManeuver[] {
  const result: FlatManeuver[] = [];
  let offset = 0;

  for (let i = 0; i < trip.legs.length; i++) {
    const leg = trip.legs[i]!;
    for (const maneuver of leg.maneuvers) {
      result.push({
        maneuver,
        legIndex: i,
        globalBeginShapeIndex: offset + maneuver.begin_shape_index,
        globalEndShapeIndex: offset + maneuver.end_shape_index,
      });
    }
    const lastManeuver = leg.maneuvers[leg.maneuvers.length - 1];
    if (lastManeuver && i < trip.legs.length - 1) {
      offset += lastManeuver.end_shape_index;
    }
  }

  return result;
}

function haversineDistance(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number
): number {
  const R = 6371000;
  const phi1 = (lat1 * Math.PI) / 180;
  const phi2 = (lat2 * Math.PI) / 180;
  const dPhi = ((lat2 - lat1) * Math.PI) / 180;
  const dLambda = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dPhi / 2) ** 2 +
    Math.cos(phi1) * Math.cos(phi2) * Math.sin(dLambda / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function findClosestShapeIndex(
  lat: number,
  lng: number,
  geometry: number[][]
): number {
  let minDist = Infinity;
  let closestIndex = 0;
  for (let i = 0; i < geometry.length; i++) {
    const point = geometry[i]!;
    const dist = haversineDistance(lat, lng, point[0]!, point[1]!);
    if (dist < minDist) {
      minDist = dist;
      closestIndex = i;
    }
  }
  return closestIndex;
}

function findCurrentManeuverIndex(
  shapeIndex: number,
  flatManeuvers: FlatManeuver[]
): number {
  for (let i = 0; i < flatManeuvers.length; i++) {
    const fm = flatManeuvers[i]!;
    if (
      shapeIndex >= fm.globalBeginShapeIndex &&
      shapeIndex < fm.globalEndShapeIndex
    ) {
      return i;
    }
  }
  return flatManeuvers.length - 1;
}

function distanceAlongPath(
  geometry: number[][],
  startIndex: number,
  endIndex: number
): number {
  let dist = 0;
  const end = Math.min(endIndex, geometry.length - 1);
  for (let i = startIndex; i < end; i++) {
    const a = geometry[i]!;
    const b = geometry[i + 1]!;
    dist += haversineDistance(a[0]!, a[1]!, b[0]!, b[1]!);
  }
  return dist;
}

export const useNavigation = () => {
  const isNavigating = useNavigationStore((state) => state.isNavigating);
  const isDemoMode = useNavigationStore((state) => state.isDemoMode);
  const trip = useNavigationStore((state) => state.trip);
  const geometry = useNavigationStore((state) => state.geometry);
  const updatePosition = useNavigationStore((state) => state.updatePosition);
  const setCurrentManeuverIndex = useNavigationStore(
    (state) => state.setCurrentManeuverIndex
  );
  const setDistanceToNextTurn = useNavigationStore(
    (state) => state.setDistanceToNextTurn
  );
  const setRemainingStats = useNavigationStore(
    (state) => state.setRemainingStats
  );

  const watchIdRef = useRef<number | null>(null);

  const flatManeuvers = useMemo(
    () => (trip ? flattenManeuvers(trip) : []),
    [trip]
  );

  useEffect(() => {
    if (!isNavigating || !geometry || flatManeuvers.length === 0 || isDemoMode) {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
      return;
    }

    if (!navigator.geolocation) return;

    watchIdRef.current = navigator.geolocation.watchPosition(
      (pos) => {
        const { latitude, longitude, heading } = pos.coords;
        updatePosition(latitude, longitude, heading ?? 0);

        const shapeIndex = findClosestShapeIndex(latitude, longitude, geometry);
        const maneuverIdx = findCurrentManeuverIndex(shapeIndex, flatManeuvers);
        setCurrentManeuverIndex(maneuverIdx);

        const currentFM = flatManeuvers[maneuverIdx]!;
        const distToTurn = distanceAlongPath(
          geometry,
          shapeIndex,
          currentFM.globalEndShapeIndex
        );
        setDistanceToNextTurn(distToTurn);

        const remainingManeuvers = flatManeuvers.slice(maneuverIdx);
        const remainingTime = remainingManeuvers.reduce(
          (sum, fm) => sum + fm.maneuver.time,
          0
        );
        const remainingDist = remainingManeuvers.reduce(
          (sum, fm) => sum + fm.maneuver.length,
          0
        );
        setRemainingStats(remainingTime, remainingDist);
      },
      (err) => console.error('Geolocation error:', err),
      { enableHighAccuracy: true, maximumAge: 1000 }
    );

    return () => {
      if (watchIdRef.current !== null) {
        navigator.geolocation.clearWatch(watchIdRef.current);
        watchIdRef.current = null;
      }
    };
  }, [
    isNavigating,
    isDemoMode,
    geometry,
    flatManeuvers,
    updatePosition,
    setCurrentManeuverIndex,
    setDistanceToNextTurn,
    setRemainingStats,
  ]);

  return { flatManeuvers };
};
