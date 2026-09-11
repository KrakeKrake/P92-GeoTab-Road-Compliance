import type { Trip } from '@/components/types';
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

interface NavigationState {
  isNavigating: boolean;
  isDemoMode: boolean;
  isRerouting: boolean;
  trip: Trip | null;
  geometry: number[][] | null;
  currentManeuverIndex: number;
  currentPosition: [number, number] | null; // [lat, lng]
  heading: number;
  distanceToNextTurn: number; // meters
  remainingTime: number; // seconds
  remainingDistance: number; // km
}

interface NavigationActions {
  startNavigation: (trip: Trip, geometry: number[][], demoMode?: boolean) => void;
  stopNavigation: () => void;
  updatePosition: (lat: number, lng: number, heading: number) => void;
  setCurrentManeuverIndex: (index: number) => void;
  setDistanceToNextTurn: (distance: number) => void;
  setRemainingStats: (time: number, distance: number) => void;
  setRerouting: (val: boolean) => void;
  updateRoute: (trip: Trip, geometry: number[][]) => void;
}

type NavigationStore = NavigationState & NavigationActions;

export const useNavigationStore = create<NavigationStore>()(
  devtools(
    immer((set) => ({
      isNavigating: false,
      isDemoMode: false,
      isRerouting: false,
      trip: null,
      geometry: null,
      currentManeuverIndex: 0,
      currentPosition: null,
      heading: 0,
      distanceToNextTurn: 0,
      remainingTime: 0,
      remainingDistance: 0,

      startNavigation: (trip, geometry, demoMode = false) =>
        set(
          (state) => {
            state.isNavigating = true;
            state.isDemoMode = demoMode;
            state.isRerouting = false;
            state.trip = trip;
            state.geometry = geometry;
            state.currentManeuverIndex = 0;
            state.currentPosition = null;
            state.heading = 0;
            state.distanceToNextTurn = 0;
            state.remainingTime = trip.summary.time;
            state.remainingDistance = trip.summary.length;
          },
          undefined,
          'startNavigation'
        ),

      stopNavigation: () =>
        set(
          (state) => {
            state.isNavigating = false;
            state.isDemoMode = false;
            state.isRerouting = false;
            state.trip = null;
            state.geometry = null;
            state.currentManeuverIndex = 0;
            state.currentPosition = null;
          },
          undefined,
          'stopNavigation'
        ),

      updatePosition: (lat, lng, heading) =>
        set(
          (state) => {
            state.currentPosition = [lat, lng];
            state.heading = heading;
          },
          undefined,
          'updatePosition'
        ),

      setCurrentManeuverIndex: (index) =>
        set(
          (state) => {
            state.currentManeuverIndex = index;
          },
          undefined,
          'setCurrentManeuverIndex'
        ),

      setDistanceToNextTurn: (distance) =>
        set(
          (state) => {
            state.distanceToNextTurn = distance;
          },
          undefined,
          'setDistanceToNextTurn'
        ),

      setRemainingStats: (time, distance) =>
        set(
          (state) => {
            state.remainingTime = time;
            state.remainingDistance = distance;
          },
          undefined,
          'setRemainingStats'
        ),

      setRerouting: (val) =>
        set(
          (state) => {
            state.isRerouting = val;
          },
          undefined,
          'setRerouting'
        ),

      // Updates trip + geometry without resetting currentPosition — used by rerouting
      updateRoute: (trip, geometry) =>
        set(
          (state) => {
            state.trip = trip;
            state.geometry = geometry;
            state.currentManeuverIndex = 0;
            state.distanceToNextTurn = 0;
            state.isRerouting = false;
            state.remainingTime = trip.summary.time;
            state.remainingDistance = trip.summary.length;
          },
          undefined,
          'updateRoute'
        ),
    })),
    { name: 'navigation-store' }
  )
);
