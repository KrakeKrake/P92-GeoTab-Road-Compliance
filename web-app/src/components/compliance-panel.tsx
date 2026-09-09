import { UserChip } from './user-chip';
import { VehicleCompliance } from './vehicle-compliance';
import { AppliedVehicleSummary } from './applied-vehicle-summary';

export const CompliancePanel = () => {
  return (
    <aside className="h-screen w-[380px] shrink-0 overflow-y-auto border-l border-border bg-background">

      <div className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-background p-4">
        <h2 className="text-lg font-semibold text-foreground">
          Compliance Engine
        </h2>

        <UserChip />
      </div>

      <VehicleCompliance />

      <AppliedVehicleSummary />

    </aside>
  );
};