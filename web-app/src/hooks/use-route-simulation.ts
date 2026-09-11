import { useNavigationStore } from '@/stores/navigation-store';
import type { Trip } from '@/components/types';

const TICK_MS = 100;
const SIMULATION_DURATION_MS = 60_000;

// ── Geometry math ─────────────────────────────────────────────────────────────

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

function bearing(lat1: number, lng1: number, lat2: number, lng2: number): number {
  const dLng = ((lng2 - lng1) * Math.PI) / 180;
  const lat1R = (lat1 * Math.PI) / 180;
  const lat2R = (lat2 * Math.PI) / 180;
  const y = Math.sin(dLng) * Math.cos(lat2R);
  const x =
    Math.cos(lat1R) * Math.sin(lat2R) -
    Math.sin(lat1R) * Math.cos(lat2R) * Math.cos(dLng);
  return (Math.atan2(y, x) * 180) / Math.PI;
}

function buildCumDist(geom: number[][]): number[] {
  const cum = [0];
  for (let i = 1; i < geom.length; i++) {
    const p = geom[i - 1]!;
    const q = geom[i]!;
    cum.push(cum[i - 1]! + haversineMeters(p[0]!, p[1]!, q[0]!, q[1]!));
  }
  return cum;
}

function positionAt(
  traveled: number,
  cumDist: number[],
  geom: number[][]
): { lat: number; lng: number; segIdx: number } {
  const total = cumDist[cumDist.length - 1]!;
  traveled = Math.min(traveled, total);
  for (let i = 1; i < cumDist.length; i++) {
    if (traveled <= cumDist[i]!) {
      const t = (traveled - cumDist[i - 1]!) / (cumDist[i]! - cumDist[i - 1]!);
      const p = geom[i - 1]!;
      const q = geom[i]!;
      return {
        lat: p[0]! + t * (q[0]! - p[0]!),
        lng: p[1]! + t * (q[1]! - p[1]!),
        segIdx: i - 1,
      };
    }
  }
  const last = geom[geom.length - 1]!;
  return { lat: last[0]!, lng: last[1]!, segIdx: geom.length - 1 };
}

// ── Module-level interval — survives component unmounts ───────────────────────

let activeIntervalId: ReturnType<typeof setInterval> | null = null;

function clearActiveInterval() {
  if (activeIntervalId != null) {
    clearInterval(activeIntervalId);
    activeIntervalId = null;
  }
}

// Stop the simulation whenever navigation ends externally (e.g. user presses Stop)
useNavigationStore.subscribe((state, prev) => {
  if (!state.isNavigating && prev.isNavigating) clearActiveInterval();
});

export function stopSimulation(): void {
  clearActiveInterval();
}

// ── Public API ────────────────────────────────────────────────────────────────

export function simulate(
  trip: Trip,
  geometry: number[][],
  durationMs: number = SIMULATION_DURATION_MS
): void {
  clearActiveInterval();

  // Use getState() so we never depend on a hook reference that could unmount
  useNavigationStore.getState().startNavigation(trip, geometry, true);

  const maneuvers = trip.legs[0]!.maneuvers;
  const cumDist = buildCumDist(geometry);
  const totalDist = cumDist[cumDist.length - 1]!;
  const totalTicks = durationMs / TICK_MS;
  const distPerTick = totalDist / totalTicks;

  // Prime first frame
  const p0 = geometry[0]!;
  const p1 = geometry[1] ?? p0;
  useNavigationStore.getState().updatePosition(
    p0[0]!, p0[1]!, bearing(p0[0]!, p0[1]!, p1[0]!, p1[1]!)
  );
  useNavigationStore.getState().setDistanceToNextTurn(maneuvers[0]!.length * 1000);

  let tick = 0;

  activeIntervalId = setInterval(() => {
    tick++;
    const traveled = Math.min(tick * distPerTick, totalDist);

    const store = useNavigationStore.getState();

    const { lat, lng, segIdx } = positionAt(traveled, cumDist, geometry);
    const nextSeg = Math.min(segIdx + 1, geometry.length - 1);
    const nextPt = geometry[nextSeg]!;
    store.updatePosition(lat, lng, bearing(lat, lng, nextPt[0]!, nextPt[1]!));

    let mIdx = 0;
    for (let i = maneuvers.length - 1; i >= 0; i--) {
      if (segIdx >= maneuvers[i]!.begin_shape_index) {
        mIdx = i;
        break;
      }
    }
    store.setCurrentManeuverIndex(mIdx);

    const endOfManeuver = cumDist[maneuvers[mIdx]!.end_shape_index] ?? totalDist;
    store.setDistanceToNextTurn(Math.max(0, endOfManeuver - traveled));

    const remaining = 1 - traveled / totalDist;
    store.setRemainingStats(
      Math.max(0, trip.summary.time * remaining),
      Math.max(0, trip.summary.length * remaining)
    );

    if (tick >= totalTicks) {
      store.setCurrentManeuverIndex(maneuvers.length - 1);
      store.setDistanceToNextTurn(0);
      clearActiveInterval();
    }
  }, TICK_MS);
}

// Resume the simulation from wherever currentPosition currently sits on the route.
// Does NOT call startNavigation — position and trip are preserved as-is.
export function resumeFromCurrentPosition(durationMs: number = SIMULATION_DURATION_MS): void {
  const { trip, geometry, currentPosition, isDemoMode } = useNavigationStore.getState();
  if (!trip || !geometry || !isDemoMode) return;

  clearActiveInterval();

  const maneuvers = trip.legs[0]!.maneuvers;
  const cumDist = buildCumDist(geometry);
  const totalDist = cumDist[cumDist.length - 1]!;
  const totalTicks = durationMs / TICK_MS;
  const distPerTick = totalDist / totalTicks;

  // Find closest geometry point to current position to determine start offset
  let startTick = 0;
  if (currentPosition) {
    let closest = 0;
    let minDist = Infinity;
    for (let i = 0; i < geometry.length; i++) {
      const d = haversineMeters(currentPosition[0], currentPosition[1], geometry[i]![0]!, geometry[i]![1]!);
      if (d < minDist) { minDist = d; closest = i; }
    }
    startTick = Math.round((cumDist[closest] ?? 0) / distPerTick);
  }

  let tick = startTick;

  activeIntervalId = setInterval(() => {
    tick++;
    const traveled = Math.min(tick * distPerTick, totalDist);

    const store = useNavigationStore.getState();

    const { lat, lng, segIdx } = positionAt(traveled, cumDist, geometry);
    const nextSeg = Math.min(segIdx + 1, geometry.length - 1);
    const nextPt = geometry[nextSeg]!;
    store.updatePosition(lat, lng, bearing(lat, lng, nextPt[0]!, nextPt[1]!));

    let mIdx = 0;
    for (let i = maneuvers.length - 1; i >= 0; i--) {
      if (segIdx >= maneuvers[i]!.begin_shape_index) { mIdx = i; break; }
    }
    store.setCurrentManeuverIndex(mIdx);

    const endOfManeuver = cumDist[maneuvers[mIdx]!.end_shape_index] ?? totalDist;
    store.setDistanceToNextTurn(Math.max(0, endOfManeuver - traveled));

    const remaining = 1 - traveled / totalDist;
    store.setRemainingStats(
      Math.max(0, trip.summary.time * remaining),
      Math.max(0, trip.summary.length * remaining)
    );

    if (tick >= totalTicks) {
      store.setCurrentManeuverIndex(maneuvers.length - 1);
      store.setDistanceToNextTurn(0);
      clearActiveInterval();
    }
  }, TICK_MS);
}

// ── Hook wrapper (kept for components that prefer the hook interface) ──────────

export const useRouteSimulation = () => ({ simulate });
