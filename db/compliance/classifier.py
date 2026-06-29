from typing import Any, Dict, List

from .vehicle_profiles import vehicle_profiles
from .vehicle_templates import vehicle_templates

from .axle_configurations import axle_configurations
GENERAL_WIDTH_LIMIT_M = 2.5
GENERAL_HEIGHT_LIMIT_M = 4.3
GENERAL_COMBINATION_LENGTH_LIMIT_M = 19.0
GENERAL_RIGID_LENGTH_LIMIT_M = 12.5

B_DOUBLE_LENGTH_LIMIT_M = 25.0

INPUT_SANITY_LIMITS = {
    "RIGID_TRUCK": {
        "min_width_m": 2.0,
        "max_width_m": 3.0,
        "min_height_m": 2.5,
        "max_height_m": 5.0,
        "min_length_m": 5.0,
        "max_length_m": 15.0
    },
    "PM_SEMI": {
        "min_width_m": 2.0,
        "max_width_m": 3.0,
        "min_height_m": 2.5,
        "max_height_m": 5.0,
        "min_length_m": 10.0,
        "max_length_m": 25.0
    },
    "B_DOUBLE": {
        "min_width_m": 2.0,
        "max_width_m": 3.0,
        "min_height_m": 2.5,
        "max_height_m": 5.0,
        "min_length_m": 15.0,
        "max_length_m": 30.0
    }
}

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

    template = get_template(profile["template_id"])
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

    return [
        field_name
        for field_name in required_fields
        if field_name not in answers or answers[field_name] is None
    ]


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

def validate_input_dimensions(template_id: str, dimensions: Dict[str, float]) -> List[str]:
    limits = INPUT_SANITY_LIMITS.get(template_id)

    if not limits:
        return []

    errors = []

    if (
        dimensions["width_m"] < limits["min_width_m"]
        or dimensions["width_m"] > limits["max_width_m"]
    ):
        errors.append(
            f"Width {dimensions['width_m']} m is outside realistic input range "
            f"({limits['min_width_m']} m to {limits['max_width_m']} m)."
        )

    if (
        dimensions["height_m"] < limits["min_height_m"]
        or dimensions["height_m"] > limits["max_height_m"]
    ):
        errors.append(
            f"Height {dimensions['height_m']} m is outside realistic input range "
            f"({limits['min_height_m']} m to {limits['max_height_m']} m)."
        )

    if (
        dimensions["length_m"] < limits["min_length_m"]
        or dimensions["length_m"] > limits["max_length_m"]
    ):
        errors.append(
            f"Length {dimensions['length_m']} m is outside realistic input range "
            f"({limits['min_length_m']} m to {limits['max_length_m']} m)."
        )

    return errors
    
def find_axle_config(config_id: str | None):
    if not config_id:
        return None

    for template_id, configs in axle_configurations.items():
        for config in configs:
            if config["config_id"] == config_id:
                return config

    return None


def classify_hvnl(profile_id: str, axle_config_id: str | None, custom_dimensions: bool, answers: Dict[str, Any]) -> Dict[str, Any]:
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
    selected_axle_config = find_axle_config(axle_config_id)

    if not template:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Vehicle template could not be resolved from profile.",
            "warnings": ["Template not found."]
        }

    dimensions = resolve_dimensions(profile_id, custom_dimensions, answers)
    validation_errors = validate_input_dimensions(template_id, dimensions)

    if validation_errors:
        return {
            "status": "error",
            "classification": "invalid_input",
            "reason": "Input dimensions are outside acceptable range.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": validation_errors
        }

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
    selected_length_limit_m = (
    selected_axle_config["max_length_m"]
    if selected_axle_config and "max_length_m" in selected_axle_config
    else None
    )

    warnings: List[str] = []

    if template_id == "RIGID_TRUCK":
        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=selected_length_limit_m or GENERAL_RIGID_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The rigid truck exceeds common general prescribed limits and does not fall under the current Class 1 or Class 2 paths.",
                "used_dimensions": dimensions,
                "missing_fields": [],
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access",
            "reason": "The rigid truck is within common general limits.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": warnings
        }

    if template_id == "PM_SEMI":
        limit_check = evaluate_limits(
            width_m=width_m,
            height_m=height_m,
            length_m=length_m,
            width_limit_m=GENERAL_WIDTH_LIMIT_M,
            height_limit_m=GENERAL_HEIGHT_LIMIT_M,
            length_limit_m=selected_length_limit_m or GENERAL_COMBINATION_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The prime mover and semitrailer combination exceeds common general prescribed limits and does not fall under the current Class 1 or Class 2 paths.",
                "used_dimensions": dimensions,
                "missing_fields": [],
                "warnings": limit_check["reasons"]
            }

        return {
            "status": "ok",
            "classification": "general_access",
            "reason": "The prime mover and semitrailer combination is within common general limits.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": warnings
        }

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
            length_limit_m=selected_length_limit_m or B_DOUBLE_LENGTH_LIMIT_M
        )

        if limit_check["exceeds"]:
            return {
                "status": "ok",
                "classification": "class_3",
                "reason": "The B-double exceeds the prototype limits applied to this Class 2 category. Under the current prototype logic, it is flagged as Class 3 for further compliance review.",
                "used_dimensions": dimensions,
                "missing_fields": [],
                "warnings": limit_check["reasons"] + warnings
            }

        return {
            "status": "ok",
            "classification": "class_2",
            "reason": "The B-double follows the Class 2 path under the current prototype rules.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": warnings
        }

    return {
        "status": "error",
        "classification": "unknown",
        "reason": "No classification rule matched this vehicle template.",
        "used_dimensions": dimensions,
        "missing_fields": [],
        "warnings": ["Rule coverage is incomplete for this vehicle type."]
    }