from typing import Any, Dict, List

from vehicle_profiles import vehicle_profiles
from vehicle_templates import vehicle_templates


# Common general limits used by the prototype
GENERAL_WIDTH_LIMIT_M = 2.5
GENERAL_HEIGHT_LIMIT_M = 4.3
GENERAL_COMBINATION_LENGTH_LIMIT_M = 19.0
GENERAL_RIGID_LENGTH_LIMIT_M = 12.5

# Category-specific prototype limits
B_DOUBLE_LENGTH_LIMIT_M = 25.0
ROAD_TRAIN_LENGTH_LIMIT_M = 53.5
VEHICLE_CARRIER_LENGTH_LIMIT_M = 25.0
VEHICLE_CARRIER_HEIGHT_LIMIT_M = 4.6
LIVESTOCK_HEIGHT_LIMIT_M = 4.6


def get_profile(profile_id: str) -> Dict[str, Any] | None:
    return vehicle_profiles.get(profile_id)


def get_template(template_id: str) -> Dict[str, Any] | None:
    return vehicle_templates.get(template_id)


def _safe_bool(value: Any) -> bool:
    return value is True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_required_fields(profile_id: str, custom_dimensions: bool) -> List[str]:
    profile = get_profile(profile_id)
    if not profile:
        return []

    template_id = profile["template_id"]
    template = get_template(template_id)
    if not template:
        return []

    required_fields = []

    if custom_dimensions:
        required_fields.extend([
            "overall_width_m",
            "overall_height_m",
            "overall_length_m"
        ])

    for question in template["extra_questions"]:
        required_fields.append(question["name"])

    return required_fields


def get_missing_fields(profile_id: str, custom_dimensions: bool, answers: Dict[str, Any]) -> List[str]:
    required_fields = get_required_fields(profile_id, custom_dimensions)
    missing = []

    for field_name in required_fields:
        if field_name not in answers or answers[field_name] is None:
            missing.append(field_name)

    return missing


def resolve_dimensions(profile_id: str, custom_dimensions: bool, answers: Dict[str, Any]) -> Dict[str, float]:
    profile = get_profile(profile_id)
    if not profile:
        return {
            "width_m": 0.0,
            "height_m": 0.0,
            "length_m": 0.0
        }

    if custom_dimensions:
        return {
            "width_m": _safe_float(answers.get("overall_width_m")),
            "height_m": _safe_float(answers.get("overall_height_m")),
            "length_m": _safe_float(answers.get("overall_length_m"))
        }

    return {
        "width_m": profile["default_width_m"],
        "height_m": profile["default_height_m"],
        "length_m": profile["default_length_m"]
    }


def evaluate_limits(
    width_m: float,
    height_m: float,
    length_m: float,
    width_limit_m: float,
    height_limit_m: float,
    length_limit_m: float
) -> Dict[str, Any]:
    reasons = []

    if width_m > width_limit_m:
        reasons.append(f"Width {width_m} m exceeds limit of {width_limit_m} m.")

    if height_m > height_limit_m:
        reasons.append(f"Height {height_m} m exceeds limit of {height_limit_m} m.")

    if length_m > length_limit_m:
        reasons.append(f"Length {length_m} m exceeds limit of {length_limit_m} m.")

    return {
        "exceeds": len(reasons) > 0,
        "reasons": reasons
    }


def classify_hvnl(profile_id: str, custom_dimensions: bool, answers: Dict[str, Any]) -> Dict[str, Any]:
    profile = get_profile(profile_id)
    if not profile:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Unsupported vehicle profile.",
            "warnings": ["Vehicle profile not found."]
        }

    template_id = profile["template_id"]
    template = get_template(template_id)
    if not template:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Vehicle template could not be resolved from profile.",
            "warnings": ["Template not found."]
        }

    # Resolve dimensions early so we can still return them for incomplete cases
    dimensions = resolve_dimensions(profile_id, custom_dimensions, answers)

    missing_fields = get_missing_fields(profile_id, custom_dimensions, answers)
    if missing_fields:
        return {
            "status": "incomplete",
            "classification": "unknown",
            "reason": "More information is required before classification.",
            "used_dimensions": dimensions,
            "missing_fields": missing_fields,
            "warnings": []
        }

    width_m = dimensions["width_m"]
    height_m = dimensions["height_m"]
    length_m = dimensions["length_m"]

    warnings: List[str] = []

    # -------------------------
    # CLASS 1 FIRST
    # -------------------------

    # Special Purpose Vehicle:
    # If it exceeds prescribed requirements, it may follow Class 1.
    if template_id == "SPV":
        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=GENERAL_RIGID_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_1",
                "reason": "A special purpose vehicle exceeding prescribed requirements may follow the Class 1 path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "A special purpose vehicle within common general limits may be general access.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # OSOM candidate:
    # If it exceeds prescribed requirements and is carrying a large indivisible item,
    # and is not a B-double or road train, it may follow Class 1.
    if template_id == "OSOM_CANDIDATE":
        large_indivisible_item = _safe_bool(answers.get("large_indivisible_item"))
        is_b_double_or_road_train = _safe_bool(answers.get("is_b_double_or_road_train"))

        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=GENERAL_COMBINATION_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"] and large_indivisible_item and not is_b_double_or_road_train:
            return {
                "status": "ok",
                "classification": "class_1",
                "reason": "The vehicle exceeds prescribed requirements and may follow the Class 1 OSOM path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"]
            }

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The vehicle exceeds prescribed requirements but does not meet the current Class 1 path conditions.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "The vehicle is within common general limits.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # -------------------------
    # CLASS 2 NEXT
    # -------------------------

    # B-double: Class 2 if it complies with the prescribed limits applying to it.
    if template_id == "B_DOUBLE":
        pbs_vehicle = _safe_bool(answers.get("pbs_vehicle"))
        if pbs_vehicle:
            warnings.append("PBS flag noted. Detailed PBS handling is not implemented yet.")

        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=B_DOUBLE_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The B-double exceeds the prototype prescribed limits applying to this Class 2 category, so it falls to the Class 3 path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"] + warnings
            }

        return {
            "status": "ok",
            "classification": "class_2",
            "reason": "The B-double fits the prototype prescribed limits for its Class 2 category.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # Road train: Class 2 if it complies with the prescribed limits applying to it.
    if template_id == "ROAD_TRAIN":
        pbs_vehicle = _safe_bool(answers.get("pbs_vehicle"))
        if pbs_vehicle:
            warnings.append("PBS flag noted. Detailed PBS handling is not implemented yet.")

        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=ROAD_TRAIN_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The road train exceeds the prototype prescribed limits applying to this Class 2 category, so it falls to the Class 3 path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"] + warnings
            }

        return {
            "status": "ok",
            "classification": "class_2",
            "reason": "The road train fits the prototype prescribed limits for its Class 2 category.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # PBS vehicle: keep simple for now.
    if template_id == "PBS_VEHICLE":
        return {
            "status": "ok",
            "classification": "class_2",
            "reason": "PBS vehicle follows the Class 2 path.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # Vehicle carrier:
    # Class 2 if >19m or >4.3m and still within its prototype prescribed carrier limits.
    if template_id == "VEHICLE_CARRIER":
        carrier_limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=VEHICLE_CARRIER_HEIGHT_LIMIT_M,
            length_limit_m=VEHICLE_CARRIER_LENGTH_LIMIT_M
        )

        if carrier_limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The vehicle carrier exceeds the prototype prescribed limits applying to this Class 2 category, so it falls to the Class 3 path.",
                "used_dimensions": dimensions,
                "warnings": carrier_limit_check["reasons"]
            }

        if length_m > 19.0 or height_m > 4.3:
            return {
                "status": "ok",
                "classification": "class_2",
                "reason": "The vehicle carrier is over 19 m or over 4.3 m and fits the prototype Class 2 carrier limits.",
                "used_dimensions": dimensions,
                "warnings": warnings
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "The vehicle carrier is within common general limits.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # Livestock vehicle:
    # Class 2 if >4.3m and still within prototype livestock height limit.
    if template_id == "LIVESTOCK_VEHICLE":
        livestock_limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=LIVESTOCK_HEIGHT_LIMIT_M,
            length_limit_m=GENERAL_COMBINATION_LENGTH_LIMIT_M
        )

        if livestock_limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The livestock vehicle exceeds the prototype prescribed limits applying to this Class 2 category, so it falls to the Class 3 path.",
                "used_dimensions": dimensions,
                "warnings": livestock_limit_check["reasons"]
            }

        if height_m > 4.3:
            return {
                "status": "ok",
                "classification": "class_2",
                "reason": "The livestock vehicle is over 4.3 m high and fits the prototype Class 2 livestock limits.",
                "used_dimensions": dimensions,
                "warnings": warnings
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "The livestock vehicle is within common general limits.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # -------------------------
    # CLASS 3 FALLBACK / GENERAL ACCESS
    # -------------------------

    # Rigid truck
    if template_id == "RIGID_TRUCK":
        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=GENERAL_RIGID_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The rigid truck exceeds common general prescribed limits and is not on a Class 1 or Class 2 path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "The rigid truck is within common general limits.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # Prime mover + semitrailer
    if template_id == "PM_SEMI":
        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=GENERAL_COMBINATION_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The prime mover and semitrailer combination exceeds common general prescribed limits and is not on a Class 1 or Class 2 path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "The prime mover and semitrailer combination is within common general limits.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    # Rigid truck + dog trailer
    if template_id == "RIGID_DOG":
        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=GENERAL_COMBINATION_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The rigid truck and dog trailer combination exceeds common general prescribed limits and is not on a Class 1 or Class 2 path.",
                "used_dimensions": dimensions,
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access_candidate",
            "reason": "The rigid truck and dog trailer combination is within common general limits.",
            "used_dimensions": dimensions,
            "warnings": warnings
        }

    return {
        "status": "error",
        "classification": "unknown",
        "reason": "No classification rule matched this vehicle template.",
        "warnings": ["Rule coverage is incomplete for this vehicle type."]
    }