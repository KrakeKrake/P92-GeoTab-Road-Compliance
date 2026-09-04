import { useComplianceStore } from '@/stores/compliance-store';

function formatVehicleClass(vehicleClass: string) {
  if (vehicleClass === 'general_access') {
    return 'General Access';
  }

  if (vehicleClass === 'class_1') {
    return 'Class 1';
  }

  if (vehicleClass === 'class_2') {
    return 'Class 2';
  }

  if (vehicleClass === 'class_3') {
    return 'Class 3';
  }

  return vehicleClass;
}

export const AppliedVehicleSummary = () => {
  const appliedVehicle = useComplianceStore(
    (state) => state.appliedVehicle
  );

  if (!appliedVehicle) {
    return (
      <div className="border-t border-border p-4">
        <div className="rounded-md bg-muted p-3">
          <p className="text-sm font-medium text-foreground">
            No Vehicle Applied
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            Complete a successful compliance check before
            planning a heavy vehicle route.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="border-t border-border p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Applied Vehicle
          </h3>

          <p className="mt-1 text-xs text-muted-foreground">
            This vehicle is ready for routing.
          </p>
        </div>

        <div className="flex h-7 w-7 items-center justify-center rounded-full bg-green-600 text-xs font-bold text-white">
          ✓
        </div>
      </div>

      <div className="overflow-hidden rounded-md border border-border">

        {/* Vehicle */}
        <div className="border-b border-border px-3 py-3">
          <p className="text-sm font-semibold text-foreground">
            {appliedVehicle.profileName}
          </p>

          <p className="mt-1 text-xs text-muted-foreground">
            {appliedVehicle.vehicleType}
          </p>
        </div>

        {/* Class */}
        <div className="flex items-center justify-between border-b border-border px-3 py-2 text-sm">
          <span className="text-muted-foreground">
            Vehicle Class
          </span>

          <span className="font-medium text-foreground">
            {formatVehicleClass(
              appliedVehicle.vehicleClass
            )}
          </span>
        </div>

        {/* Axle */}
        <div className="flex items-center justify-between border-b border-border px-3 py-2 text-sm">
          <span className="text-muted-foreground">
            Axle
          </span>

          <span className="max-w-[180px] text-right font-medium text-foreground">
            {appliedVehicle.axleConfigName}
          </span>
        </div>

        {/* Mass scheme */}
        <div className="flex items-center justify-between border-b border-border px-3 py-2 text-sm">
          <span className="text-muted-foreground">
            Mass Scheme
          </span>

          <span className="font-medium text-foreground">
            {appliedVehicle.massScheme}
          </span>
        </div>

        {/* Operating mass */}
        <div className="flex items-center justify-between border-b border-border px-3 py-2 text-sm">
          <span className="text-muted-foreground">
            Operating Mass
          </span>

          <span className="font-medium text-foreground">
            {appliedVehicle.operatingMassT} t
          </span>
        </div>

        {/* Dimensions */}
        <div className="px-3 py-3">
          <p className="mb-2 text-xs font-medium text-muted-foreground">
            Routing Dimensions
          </p>

          <div className="grid grid-cols-3 gap-2 text-center">
            <div className="rounded-md bg-muted p-2">
              <p className="text-xs text-muted-foreground">
                Width
              </p>

              <p className="mt-1 text-sm font-medium">
                {appliedVehicle.widthM} m
              </p>
            </div>

            <div className="rounded-md bg-muted p-2">
              <p className="text-xs text-muted-foreground">
                Height
              </p>

              <p className="mt-1 text-sm font-medium">
                {appliedVehicle.heightM} m
              </p>
            </div>

            <div className="rounded-md bg-muted p-2">
              <p className="text-xs text-muted-foreground">
                Length
              </p>

              <p className="mt-1 text-sm font-medium">
                {appliedVehicle.lengthM} m
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};