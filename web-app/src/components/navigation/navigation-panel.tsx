import React from 'react';
import { X, Clock, MoveHorizontal, RotateCcw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useNavigationStore } from '@/stores/navigation-store';
import { useNavigation } from '@/hooks/use-navigation';
import { useKeyboardNavigation } from '@/hooks/use-keyboard-navigation';
import { getManeuverIcon } from '@/utils/get-maneuver-icon';
import { formatDuration } from '@/utils/date-time';

const formatDistance = (meters: number): string => {
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toFixed(1)} km`;
};

export const NavigationPanel = () => {
  const isNavigating = useNavigationStore((state) => state.isNavigating);
  const trip = useNavigationStore((state) => state.trip);
  const currentManeuverIndex = useNavigationStore(
    (state) => state.currentManeuverIndex
  );
  const distanceToNextTurn = useNavigationStore(
    (state) => state.distanceToNextTurn
  );
  const remainingTime = useNavigationStore((state) => state.remainingTime);
  const remainingDistance = useNavigationStore(
    (state) => state.remainingDistance
  );
  const stopNavigation = useNavigationStore((state) => state.stopNavigation);
  const isRerouting = useNavigationStore((state) => state.isRerouting);
  const { flatManeuvers } = useNavigation();
  useKeyboardNavigation();

  if (!isNavigating || !trip || flatManeuvers.length === 0) return null;

  const currentFM = flatManeuvers[currentManeuverIndex];
  const nextFM = flatManeuvers[currentManeuverIndex + 1];

  if (!currentFM) return null;

  // Show the UPCOMING maneuver (what to do next) as the primary card.
  // distanceToNextTurn is already the distance to where the next action is needed.
  const upcomingFM = nextFM ?? currentFM;
  const afterFM = nextFM ? flatManeuvers[currentManeuverIndex + 2] : null;

  const UpcomingIcon = getManeuverIcon(upcomingFM.maneuver.type);
  const AfterIcon = afterFM ? getManeuverIcon(afterFM.maneuver.type) : null;

  return (
    <div className="absolute top-0 left-0 right-0 z-50 flex flex-col bg-slate-900 text-white shadow-xl select-none">
      {isRerouting && (
        <div className="flex items-center gap-2 px-4 py-2 bg-amber-600 text-white text-sm font-semibold animate-pulse">
          <RotateCcw size={14} className="animate-spin" />
          Recalculating route…
        </div>
      )}
      <div className="flex items-center gap-4 px-4 py-3">
        <UpcomingIcon size={48} className="shrink-0 text-white" />
        <div className="flex-1 min-w-0">
          <p className="text-3xl font-bold leading-tight">
            {formatDistance(distanceToNextTurn)}
          </p>
          <p className="text-sm text-slate-300 truncate">
            {upcomingFM.maneuver.instruction}
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-slate-700 shrink-0"
          onClick={stopNavigation}
          aria-label="Stop navigation"
        >
          <X size={24} />
        </Button>
      </div>

      {afterFM && AfterIcon && (
        <div className="flex items-center gap-3 px-4 py-2 bg-slate-800 border-t border-slate-700">
          <AfterIcon size={18} className="shrink-0 text-slate-400" />
          <p className="text-sm text-slate-300 truncate">
            Then: {afterFM.maneuver.instruction}
          </p>
        </div>
      )}

      <div className="flex items-center justify-between px-4 py-2 bg-slate-800 border-t border-slate-700">
        <div className="flex items-center gap-1.5 text-sm text-slate-300">
          <Clock size={14} className="text-slate-400" />
          <span>{formatDuration(remainingTime)} remaining</span>
        </div>
        <div className="flex items-center gap-1.5 text-sm text-slate-300">
          <MoveHorizontal size={14} className="text-slate-400" />
          <span>{remainingDistance.toFixed(1)} km</span>
        </div>
        <Button size="sm" variant="destructive" onClick={stopNavigation}>
          End
        </Button>
      </div>
    </div>
  );
};
