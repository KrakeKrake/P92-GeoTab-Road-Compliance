import { create } from 'zustand';

export interface AppliedVehicle {
  profileId: string;
  profileName: string;

  templateId: string;
  vehicleType: string;

  vehicleClass: string;

  axleConfigId: string;
  axleConfigName: string;

  massScheme: string;
  accessPath: string;

  widthM: number;
  heightM: number;
  lengthM: number;

  operatingMassT: number;
}

export interface RoutingRestriction {
  restrictionId: string;
  restrictionName: string;

  source: string;
  restrictionType: string;

  geometryRef: string | null;
  isDerived: boolean;

  conditionCode: string | null;
}

export interface RoutingPreset {
  goodsTypeId: string;
  goodsDisplayName: string;

  /*
   * null means:
   * keep the normal network selected from
   * the vehicle configuration.
   */
  networkOverrideKey: string | null;

  networkRuleNote: string | null;

  additionalRestrictions: RoutingRestriction[];

  reason: string;
}

interface ComplianceState {
  appliedVehicle: AppliedVehicle | null;

  routingPreset: RoutingPreset | null;

  setAppliedVehicle: (
    vehicle: AppliedVehicle
  ) => void;

  clearAppliedVehicle: () => void;

  setRoutingPreset: (
    preset: RoutingPreset
  ) => void;

  clearRoutingPreset: () => void;
}

export const useComplianceStore =
  create<ComplianceState>((set) => ({
    appliedVehicle: null,

    routingPreset: null,

    setAppliedVehicle: (vehicle) =>
      set({
        appliedVehicle: vehicle,
      }),

    clearAppliedVehicle: () =>
      set({
        appliedVehicle: null,
        routingPreset: null,
      }),

    setRoutingPreset: (preset) =>
      set({
        routingPreset: preset,
      }),

    clearRoutingPreset: () =>
      set({
        routingPreset: null,
      }),
  }));