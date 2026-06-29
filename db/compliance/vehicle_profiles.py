vehicle_profiles = {

    # =========================
    # RIGID TRUCK PROFILES
    # =========================

    "STANDARD_LR_RIGID": {
        "profile_id": "STANDARD_LR_RIGID",
        "display_name": "Light Rigid Truck (2 Axle, ≤8t GVM)",
        "template_id": "RIGID_TRUCK",

        # Core attributes (IMPORTANT)
        "vehicle_family": "rigid_truck",
        "combination_type": "single_vehicle",
        "axle_count": 2,
        "gvm_category": "light",  # ≤8t

        # Dimensions (approx realistic)
        "default_width_m": 2.5,
        "default_height_m": 3.5,
        "default_length_m": 8.0,

        "allow_custom_dimensions": True
    },

    "STANDARD_MR_RIGID": {
        "profile_id": "STANDARD_MR_RIGID",
        "display_name": "Medium Rigid Truck (2 Axle, >8t GVM)",
        "template_id": "RIGID_TRUCK",

        "vehicle_family": "rigid_truck",
        "combination_type": "single_vehicle",
        "axle_count": 2,
        "gvm_category": "medium",  # >8t

        "default_width_m": 2.5,
        "default_height_m": 4.0,
        "default_length_m": 10.0,

        "allow_custom_dimensions": True
    },

    "STANDARD_HR_RIGID": {
        "profile_id": "STANDARD_HR_RIGID",
        "display_name": "Heavy Rigid Truck (3+ Axle, >8t GVM)",
        "template_id": "RIGID_TRUCK",

        "vehicle_family": "rigid_truck",
        "combination_type": "single_vehicle",
        "axle_count": 3,
        "gvm_category": "heavy",

        # Based on NHVR typical limits (≤12.5m)
        "default_width_m": 2.5,
        "default_height_m": 4.3,
        "default_length_m": 12.5,

        "allow_custom_dimensions": True
    },

    # =========================
    # PRIME MOVER + SEMI
    # =========================

    "STANDARD_PM_SEMI": {
        "profile_id": "STANDARD_PM_SEMI",
        "display_name": "Prime Mover + Semitrailer",
        "template_id": "PM_SEMI",

        "vehicle_family": "articulated",
        "combination_type": "single_trailer",
        "axle_configurable": True,
        "possible_axle_configs": ["5_axle", "6_axle"],
        "gvm_category": "heavy_combination",

        # NHVR general access ~19m
        "default_width_m": 2.5,
        "default_height_m": 4.3,
        "default_length_m": 19.0,

        "allow_custom_dimensions": True
    },

    # =========================
    # B-DOUBLE (CLASS 2)
    # =========================

    "STANDARD_B_DOUBLE": {
        "profile_id": "STANDARD_B_DOUBLE",
        "display_name": "B-Double Combination",
        "template_id": "B_DOUBLE",

        "vehicle_family": "multi_combination",
        "combination_type": "multi_trailer",
        "axle_configurable": True,
        "possible_axle_configs": ["7_axle", "8_axle", "9_axle"],
        "gvm_category": "multi_combination",

        # NHVR ~26m limit for B-double
        "default_width_m": 2.5,
        "default_height_m": 4.3,
        "default_length_m": 26.0,

        "allow_custom_dimensions": True
    }
}