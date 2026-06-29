vehicle_templates = {
    "RIGID_TRUCK": {
        "display_name": "Rigid truck",
        "base_type": "rigid",
        "extra_questions": []
    },

    "PM_SEMI": {
        "display_name": "Prime mover + semitrailer",
        "base_type": "articulated",
        "extra_questions": []
    },

    "B_DOUBLE": {
        "display_name": "B-double",
        "base_type": "b_double",
        "extra_questions": [
            {
                "name": "pbs_vehicle",
                "type": "bool",
                "label": "Is this a PBS vehicle?"
            }
        ]
    }
}