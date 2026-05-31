axle_configurations = {
    "RIGID_TRUCK": [
        {
            "config_id": "RIGID_2_AXLE",
            "display_name": "2 Axle Rigid Truck",
            "max_length_m": 12.5,
            "gml_mass_t": 15.0,
            "cml_mass_t": None,
            "hml_mass_t": None,
            "access_path": "general_access"
        },
        {
            "config_id": "RIGID_3_AXLE",
            "display_name": "3 Axle Rigid Truck",
            "max_length_m": 12.5,
            "gml_mass_t": 22.5,
            "cml_mass_t": 23.0,
            "hml_mass_t": None,
            "access_path": "general_access"
        },
        {
            "config_id": "RIGID_4_AXLE",
            "display_name": "4 Axle Rigid Truck",
            "max_length_m": 12.5,
            "gml_mass_t": 26.0,
            "cml_mass_t": 27.0,
            "hml_mass_t": None,
            "access_path": "general_access"
        },
        {
            "config_id": "RIGID_4_AXLE_TWINSTEER",
            "display_name": "4 Axle Twinsteer Rigid Truck",
            "max_length_m": 12.5,
            "gml_mass_t": 26.5,
            "cml_mass_t": 27.0,
            "hml_mass_t": None,
            "access_path": "general_access",
            "note": "Add one tonne if twinsteer axle group is load sharing."
        },
        {
            "config_id": "RIGID_5_AXLE_TWINSTEER",
            "display_name": "5 Axle Twinsteer Rigid Truck",
            "max_length_m": 12.5,
            "gml_mass_t": 30.0,
            "cml_mass_t": 31.0,
            "hml_mass_t": None,
            "access_path": "general_access",
            "note": "Add one tonne if twinsteer axle group is load sharing."
        }
    ],

    "PM_SEMI": [
        {
            "config_id": "SEMI_3_AXLE_6_9_9",
            "display_name": "3 Axle Semitrailer",
            "axle_group_masses_t": [6.0, 9.0, 9.0],
            "max_length_m": 19.0,
            "gml_mass_t": 24.0,
            "cml_mass_t": None,
            "hml_mass_t": None,
            "access_path": "general_access"
        },
        {
            "config_id": "SEMI_4_AXLE_6_9_16_5",
            "display_name": "4 Axle Semitrailer",
            "axle_group_masses_t": [6.0, 9.0, 16.5],
            "max_length_m": 19.0,
            "gml_mass_t": 31.5,
            "cml_mass_t": 32.0,
            "hml_mass_t": 32.0,
            "access_path": "general_access"
        },
        {
            "config_id": "SEMI_5_AXLE_6_9_20",
            "display_name": "5 Axle Semitrailer",
            "axle_group_masses_t": [6.0, 9.0, 20.0],
            "max_length_m": 19.0,
            "gml_mass_t": 35.0,
            "cml_mass_t": 36.0,
            "hml_mass_t": 37.5,
            "access_path": "general_access"
        },
        {
            "config_id": "SEMI_5_AXLE_6_16_5_16_5",
            "display_name": "5 Axle Semitrailer",
            "axle_group_masses_t": [6.0, 16.5, 16.5],
            "max_length_m": 19.0,
            "gml_mass_t": 39.0,
            "cml_mass_t": 40.0,
            "hml_mass_t": 40.0,
            "access_path": "general_access"
        },
        {
            "config_id": "SEMI_6_AXLE_6_16_5_20",
            "display_name": "6 Axle Semitrailer",
            "axle_group_masses_t": [6.0, 16.5, 20.0],
            "max_length_m": 19.0,
            "gml_mass_t": 42.5,
            "cml_mass_t": 43.5,
            "hml_mass_t": 45.5,
            "access_path": "general_access"
        }
    ],

    "B_DOUBLE": [
        {
            "config_id": "B_DOUBLE_7_AXLE_6_16_5_16_5_16_5",
            "display_name": "7 Axle B-double",
            "axle_group_masses_t": [6.0, 16.5, 16.5, 16.5],
            "max_length_m": 19.0,
            "gml_mass_t": 55.5,
            "cml_mass_t": 57.0,
            "hml_mass_t": 57.0,
            "access_path": "class_2"
        },
        {
            "config_id": "B_DOUBLE_8_AXLE_6_16_5_20_16_5",
            "display_name": "8 Axle B-double",
            "axle_group_masses_t": [6.0, 16.5, 20.0, 16.5],
            "max_length_m": 26.0,
            "gml_mass_t": 59.0,
            "cml_mass_t": 61.0,
            "hml_mass_t": 62.5,
            "access_path": "class_2"
        },
        {
            "config_id": "B_DOUBLE_8_AXLE_6_16_5_16_5_20",
            "display_name": "8 Axle B-double",
            "axle_group_masses_t": [6.0, 16.5, 16.5, 20.0],
            "max_length_m": 26.0,
            "gml_mass_t": 59.0,
            "cml_mass_t": 61.0,
            "hml_mass_t": 62.5,
            "access_path": "class_2"
        },
        {
            "config_id": "B_DOUBLE_9_AXLE_6_16_5_20_20",
            "display_name": "9 Axle B-double",
            "axle_group_masses_t": [6.0, 16.5, 20.0, 20.0],
            "max_length_m": 26.0,
            "gml_mass_t": 62.5,
            "cml_mass_t": 64.5,
            "hml_mass_t": 68.0,
            "access_path": "class_2"
        }
    ]
}