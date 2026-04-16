vehicle_templates = {
    "RIGID_TRUCK": {
        "display_name": "Rigid truck",
        "base_type": "rigid",
        "possible_classes": ["general_access", "class_3"],
        "extra_questions": []
    },
    "RIGID_DOG": {
        "display_name": "Rigid truck + dog trailer",
        "base_type": "rigid_combination",
        "possible_classes": ["general_access", "class_3"],
        "extra_questions": []
    },
    "PM_SEMI": {
        "display_name": "Prime mover + semitrailer",
        "base_type": "articulated",
        "possible_classes": ["general_access", "class_3"],
        "extra_questions": []
    },
    "B_DOUBLE": {
        "display_name": "B-double",
        "base_type": "b_double",
        "possible_classes": ["class_2"],
        "extra_questions": [
            {
                "name": "pbs_vehicle",
                "type": "bool",
                "label": "Is this a PBS vehicle?"
            }
        ]
    },
    "ROAD_TRAIN": {
        "display_name": "Road train",
        "base_type": "road_train",
        "possible_classes": ["class_2"],
        "extra_questions": [
            {
                "name": "pbs_vehicle",
                "type": "bool",
                "label": "Is this a PBS vehicle?"
            }
        ]
    },
    "VEHICLE_CARRIER": {
        "display_name": "Vehicle carrier",
        "base_type": "vehicle_carrier",
        "possible_classes": ["general_access", "class_2"],
        "extra_questions": []
    },
    "LIVESTOCK_VEHICLE": {
        "display_name": "Livestock vehicle",
        "base_type": "livestock",
        "possible_classes": ["general_access", "class_2"],
        "extra_questions": []
    },
    "PBS_VEHICLE": {
        "display_name": "PBS vehicle",
        "base_type": "pbs",
        "possible_classes": ["class_2"],
        "extra_questions": []
    },
    "SPV": {
        "display_name": "Special purpose vehicle",
        "base_type": "spv",
        "possible_classes": ["general_access", "class_1"],
        "extra_questions": []
    },
    "OSOM_CANDIDATE": {
        "display_name": "Oversize / overmass candidate",
        "base_type": "osom",
        "possible_classes": ["class_1", "class_3"],
        "extra_questions": [
            {
                "name": "large_indivisible_item",
                "type": "bool",
                "label": "Is it carrying a large indivisible item?"
            },
            {
                "name": "is_b_double_or_road_train",
                "type": "bool",
                "label": "Is it a B-double or road train?"
            }
        ]
    }
}