import { create } from 'zustand';

/*
 * Vehicle configuration that has successfully passed
 * the Compliance Engine and is ready to be used
 * by the routing system.
 */
export interface AppliedVehicle {
  // Vehicle identity
  profileId: string;
  profileName: string;

  templateId: string;
  vehicleType: string;
  vehicleClass: string;

  // Axle configuration
  axleConfigId: string;
  axleConfigName: string;

  // Compliance information
  massScheme: string;
  accessPath: string;

  // Physical properties for routing
  widthM: number;
  heightM: number;
  lengthM: number;
  operatingMassT: number;
}

interface ComplianceState {
  /*
   * null means no vehicle has been successfully
   * validated/applied yet.
   */
  appliedVehicle: AppliedVehicle | null;

  /*
   * Save a successfully validated vehicle.
   */
  setAppliedVehicle: (
    vehicle: AppliedVehicle
  ) => void;

  /*
   * Remove the currently applied vehicle.
   */
  clearAppliedVehicle: () => void;
}

export const useComplianceStore =
  create<ComplianceState>((set) => ({
    appliedVehicle: null,

    setAppliedVehicle: (vehicle) =>
      set({
        appliedVehicle: vehicle,
      }),

    clearAppliedVehicle: () =>
      set({
        appliedVehicle: null,
      }),
  }));