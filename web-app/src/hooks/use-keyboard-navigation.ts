import { useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { useNavigationStore } from '@/stores/navigation-store';
import { stopSimulation, resumeFromCurrentPosition } from '@/hooks/use-route-simulation';
import { getValhallaUrl, parseDirectionsGeometry, VALHALLA_CLIENT_HEADERS } from '@/utils/valhalla';
import type { ValhallaRouteResponse } from '@/components/types';

// ── Tuning constants ──────────────────────────────────────────────────────────
const STEP_M       = 20;    // meters per Up/Down keypress
const TURN_DEG     = 15;    // degrees per Left/Right keypress
const OFF_ROUTE_M  = 50;    // meters off-route before rerouting
const REROUTE_DELAY_MS = 1500; // wait this long off-route before calling Valhalla

// ── Geometry helpers ──────────────────────────────────────────────────────────

function haversineMeters(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const R = 6_371_000;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

// Move a lat/lng point by `distM` metres along `bearingDeg`
function movePoint(lat: number, lng: number, bearingDeg: number, distM: number): [number, number] {
  const R   = 6_371_000;
  const d   = distM / R;
  const bR  = (bearingDeg * Math.PI) / 180;
  const la1 = (lat * Math.PI) / 180;
  const lo1 = (lng * Math.PI) / 180;
  const la2 = Math.asin(Math.sin(la1) * Math.cos(d) + Math.cos(la1) * Math.sin(d) * Math.cos(bR));
  const lo2 = lo1 + Math.atan2(Math.sin(bR) * Math.sin(d) * Math.cos(la1), Math.cos(d) - Math.sin(la1) * Math.sin(la2));
  return [(la2 * 180) / Math.PI, (lo2 * 180) / Math.PI];
}

// Closest geometry point distance (meters)
function nearestRouteDist(lat: number, lng: number, geometry: number[][]): number {
  let min = Infinity;
  for (const pt of geometry) {
    const d = haversineMeters(lat, lng, pt[0]!, pt[1]!);
    if (d < min) min = d;
  }
  return min;
}

// ── Maneuver tracking ─────────────────────────────────────────────────────────

function updateManeuverInfo(lat: number, lng: number, geometry: number[][], maneuvers: { begin_shape_index: number; end_shape_index: number; time: number; length: number }[]) {
  // Find closest geometry index to current position
  let closestIdx = 0;
  let minDist = Infinity;
  for (let i = 0; i < geometry.length; i++) {
    const d = haversineMeters(lat, lng, geometry[i]![0]!, geometry[i]![1]!);
    if (d < minDist) { minDist = d; closestIdx = i; }
  }

  // Maneuver containing this index
  let mIdx = 0;
  for (let i = maneuvers.length - 1; i >= 0; i--) {
    if (closestIdx >= maneuvers[i]!.begin_shape_index) { mIdx = i; break; }
  }

  // Distance to end of maneuver along geometry
  let dist = 0;
  const endIdx = maneuvers[mIdx]!.end_shape_index;
  for (let i = closestIdx; i < endIdx && i + 1 < geometry.length; i++) {
    dist += haversineMeters(geometry[i]![0]!, geometry[i]![1]!, geometry[i + 1]![0]!, geometry[i + 1]![1]!);
  }

  // Remaining stats (linear progress)
  const progress = closestIdx / Math.max(geometry.length - 1, 1);
  const totalTime = maneuvers.reduce((s, m) => s + m.time, 0);
  const totalDist = maneuvers.reduce((s, m) => s + m.length, 0);

  const store = useNavigationStore.getState();
  store.setCurrentManeuverIndex(mIdx);
  store.setDistanceToNextTurn(dist);
  store.setRemainingStats(Math.max(0, totalTime * (1 - progress)), Math.max(0, totalDist * (1 - progress)));
}

// ── Rerouting ─────────────────────────────────────────────────────────────────

async function fetchReroute(fromLat: number, fromLng: number, toLat: number, toLon: number): Promise<{ trip: import('@/components/types').Trip; geometry: number[][] }> {
  const body = {
    costing: 'auto',
    locations: [
      { lat: fromLat, lon: fromLng, type: 'break' },
      { lat: toLat, lon: toLon, type: 'break' },
    ],
    units: 'kilometers',
    language: 'en-US',
    id: 'reroute',
  };
  const params = new URLSearchParams({ json: JSON.stringify(body) });
  const res = await fetch(`${getValhallaUrl()}/route?${params}`, {
    headers: { 'Content-Type': 'application/json', ...VALHALLA_CLIENT_HEADERS },
    signal: AbortSignal.timeout(8000),
  });
  if (!res.ok) throw new Error(`Valhalla ${res.status}`);
  const data: ValhallaRouteResponse = await res.json();
  return { trip: data.trip, geometry: parseDirectionsGeometry(data) };
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export const useKeyboardNavigation = () => {
  const tookOverRef    = useRef(false);
  const headingRef     = useRef(0);
  const rerouteTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reroutingRef   = useRef(false);

  // Reset on each new navigation session
  useEffect(() => {
    const unsub = useNavigationStore.subscribe((s, prev) => {
      if (s.isNavigating && !prev.isNavigating) {
        tookOverRef.current   = false;
        headingRef.current    = 0;
        reroutingRef.current  = false;
        if (rerouteTimerRef.current) { clearTimeout(rerouteTimerRef.current); rerouteTimerRef.current = null; }
      }
    });
    return unsub;
  }, []);

  useEffect(() => {
    const cancelRerouteTimer = () => {
      if (rerouteTimerRef.current) { clearTimeout(rerouteTimerRef.current); rerouteTimerRef.current = null; }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      const ARROW_KEYS = ['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'];
      const isArrow = ARROW_KEYS.includes(e.key);
      const isSpace = e.key === ' ';
      if (!isArrow && !isSpace) return;

      const store = useNavigationStore.getState();
      const { isNavigating, isDemoMode, geometry, trip, currentPosition, heading } = store;
      if (!isNavigating || !isDemoMode || !geometry || !trip) return;

      e.preventDefault();

      // Space: hand control back to the auto-simulation from current position
      if (isSpace) {
        tookOverRef.current = false;
        cancelRerouteTimer();
        store.setRerouting(false);
        resumeFromCurrentPosition();
        return;
      }

      // First keypress: stop auto-simulation and take over
      if (!tookOverRef.current) {
        stopSimulation();
        tookOverRef.current  = true;
        headingRef.current   = heading;
      }

      const lat = currentPosition?.[0] ?? geometry[0]![0]!;
      const lng = currentPosition?.[1] ?? geometry[0]![1]!;

      // Left/Right: rotate heading in place
      if (e.key === 'ArrowLeft') {
        headingRef.current = (headingRef.current - TURN_DEG + 360) % 360;
        store.updatePosition(lat, lng, headingRef.current);
        return;
      }
      if (e.key === 'ArrowRight') {
        headingRef.current = (headingRef.current + TURN_DEG) % 360;
        store.updatePosition(lat, lng, headingRef.current);
        return;
      }

      // Up/Down: move forward/backward along current heading
      const distM = e.key === 'ArrowUp' ? STEP_M : -STEP_M;
      const [newLat, newLng] = movePoint(lat, lng, headingRef.current, distM);
      store.updatePosition(newLat, newLng, headingRef.current);

      // Update maneuver display from nearest route point
      const maneuvers = trip.legs[0]!.maneuvers;
      updateManeuverInfo(newLat, newLng, geometry, maneuvers);

      // Off-route detection
      if (reroutingRef.current) return; // already rerouting, skip
      const distToRoute = nearestRouteDist(newLat, newLng, geometry);

      if (distToRoute > OFF_ROUTE_M) {
        if (!rerouteTimerRef.current) {
          store.setRerouting(true);
          rerouteTimerRef.current = setTimeout(async () => {
            rerouteTimerRef.current = null;
            reroutingRef.current = true;

            const currentStore = useNavigationStore.getState();
            const pos = currentStore.currentPosition;
            if (!pos || !currentStore.trip) { reroutingRef.current = false; currentStore.setRerouting(false); return; }

            const dest = currentStore.trip.locations[currentStore.trip.locations.length - 1]!;
            const toastId = toast.loading('Recalculating route…');

            try {
              const { trip: newTrip, geometry: newGeometry } = await fetchReroute(pos[0], pos[1], dest.lat, dest.lon);
              useNavigationStore.getState().updateRoute(newTrip, newGeometry);
              toast.success('Route updated', { id: toastId });
            } catch {
              useNavigationStore.getState().setRerouting(false);
              toast.error('Could not recalculate route — check Valhalla connection', { id: toastId });
            } finally {
              reroutingRef.current = false;
            }
          }, REROUTE_DELAY_MS);
        }
      } else {
        // Back on route — cancel pending reroute
        if (rerouteTimerRef.current) {
          cancelRerouteTimer();
          store.setRerouting(false);
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => { window.removeEventListener('keydown', handleKeyDown); cancelRerouteTimer(); };
  }, []);
};
