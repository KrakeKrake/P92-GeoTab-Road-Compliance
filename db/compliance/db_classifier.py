from typing import Any, Dict, List

from sqlalchemy.orm import Session

from .db_models import (
    VehicleProfile,
    VehicleTemplate,
    TemplateQuestion,
    AxleConfiguration,
    DimensionRule,
    InputSanityRange,
)

def _safe_bool(value: Any) -> bool:
    return value is True


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_profile_from_db(db: Session, profile_id: str):
    return (
        db.query(VehicleProfile)
        .filter(VehicleProfile.profile_id == profile_id)
        .first()
    )


def get_template_from_db(db: Session, template_id: str):
    return (
        db.query(VehicleTemplate)
        .filter(VehicleTemplate.template_id == template_id)
        .first()
    )


def get_template_questions_from_db(db: Session, template_id: str):
    return (
        db.query(TemplateQuestion)
        .filter(TemplateQuestion.template_id == template_id)
        .all()
    )


def find_axle_config_from_db(db: Session, axle_config_id: str | None):
    if not axle_config_id:
        return None

    return (
        db.query(AxleConfiguration)
        .filter(AxleConfiguration.axle_config_id == axle_config_id)
        .first()
    )


def get_required_fields_from_db(
    db: Session,
    profile_id: str,
    custom_dimensions: bool
) -> List[str]:
    profile = get_profile_from_db(db, profile_id)

    if not profile:
        return []

    questions = get_template_questions_from_db(db, profile.template_id)

    required_fields = []

    if custom_dimensions:
        required_fields.extend([
            "overall_width_m",
            "overall_height_m",
            "overall_length_m"
        ])

    for question in questions:
        required_fields.append(question.question_name)

    return required_fields


def get_missing_fields_from_db(
    db: Session,
    profile_id: str,
    custom_dimensions: bool,
    answers: Dict[str, Any]
) -> List[str]:
    required_fields = get_required_fields_from_db(
        db=db,
        profile_id=profile_id,
        custom_dimensions=custom_dimensions
    )

    return [
        field_name
        for field_name in required_fields
        if field_name not in answers or answers[field_name] is None
    ]


def resolve_dimensions_from_db(
    db: Session,
    profile_id: str,
    custom_dimensions: bool,
    answers: Dict[str, Any]
) -> Dict[str, float]:
    profile = get_profile_from_db(db, profile_id)

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
        "width_m": float(profile.default_width_m),
        "height_m": float(profile.default_height_m),
        "length_m": float(profile.default_length_m)
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

def get_dimension_rule_from_db(db: Session, template_id: str):
    return (
        db.query(DimensionRule)
        .filter(DimensionRule.template_id == template_id)
        .first()
    )


def get_input_sanity_range_from_db(db: Session, template_id: str):
    return (
        db.query(InputSanityRange)
        .filter(InputSanityRange.template_id == template_id)
        .first()
    )


def validate_input_dimensions_from_db(
    db: Session,
    template_id: str,
    dimensions: Dict[str, float]
) -> List[str]:
    limits = get_input_sanity_range_from_db(db, template_id)

    if not limits:
        return []

    errors = []

    min_width = float(limits.min_width_m)
    max_width = float(limits.max_width_m)
    min_height = float(limits.min_height_m)
    max_height = float(limits.max_height_m)
    min_length = float(limits.min_length_m)
    max_length = float(limits.max_length_m)

    if dimensions["width_m"] < min_width or dimensions["width_m"] > max_width:
        errors.append(
            f"Width {dimensions['width_m']} m is outside realistic input range "
            f"({min_width} m to {max_width} m)."
        )

    if dimensions["height_m"] < min_height or dimensions["height_m"] > max_height:
        errors.append(
            f"Height {dimensions['height_m']} m is outside realistic input range "
            f"({min_height} m to {max_height} m)."
        )

    if dimensions["length_m"] < min_length or dimensions["length_m"] > max_length:
        errors.append(
            f"Length {dimensions['length_m']} m is outside realistic input range "
            f"({min_length} m to {max_length} m)."
        )

    return errors


def classify_hvnl_from_db(
    db: Session,
    profile_id: str,
    axle_config_id: str | None,
    custom_dimensions: bool,
    answers: Dict[str, Any]
) -> Dict[str, Any]:

    profile = get_profile_from_db(db, profile_id)

    if not profile:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Unsupported vehicle profile.",
            "warnings": ["Vehicle profile not found."]
        }

    template_id = profile.template_id
    template = get_template_from_db(db, template_id)
    selected_axle_config = find_axle_config_from_db(db, axle_config_id)

    if not template:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Vehicle template could not be resolved from profile.",
            "warnings": ["Template not found."]
        }

    dimensions = resolve_dimensions_from_db(
        db=db,
        profile_id=profile_id,
        custom_dimensions=custom_dimensions,
        answers=answers
    )

    validation_errors = validate_input_dimensions_from_db(
        db=db,
        template_id=template_id,
        dimensions=dimensions
    )

    if validation_errors:
        return {
            "status": "error",
            "classification": "invalid_input",
            "reason": "Input dimensions are outside acceptable range.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": validation_errors
        }

    missing_fields = get_missing_fields_from_db(
        db=db,
        profile_id=profile_id,
        custom_dimensions=custom_dimensions,
        answers=answers
    )

    if missing_fields:
        return {
            "status": "incomplete",
            "classification": "unknown",
            "reason": "More information is required before classification.",
            "used_dimensions": dimensions,
            "missing_fields": missing_fields,
            "warnings": []
        }

    dimension_rule = get_dimension_rule_from_db(db, template_id)

    if not dimension_rule:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Dimension rule not found for this vehicle template.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": ["Dimension rule coverage is incomplete."]
        }

    width_m = dimensions["width_m"]
    height_m = dimensions["height_m"]
    length_m = dimensions["length_m"]

    selected_length_limit_m = (
        float(selected_axle_config.max_length_m)
        if selected_axle_config
        else float(dimension_rule.length_limit_m)
    )

    limit_check = evaluate_limits(
        width_m=width_m,
        height_m=height_m,
        length_m=length_m,
        width_limit_m=float(dimension_rule.width_limit_m),
        height_limit_m=float(dimension_rule.height_limit_m),
        length_limit_m=selected_length_limit_m
    )

    warnings: List[str] = []

    if template_id == "B_DOUBLE":
        pbs_vehicle = _safe_bool(answers.get("pbs_vehicle"))
        if pbs_vehicle:
            warnings.append("PBS flag noted. Detailed PBS handling is not implemented yet.")

    if limit_check["exceeds"]:
        if template_id == "RIGID_TRUCK":
            reason = (
                "The rigid truck exceeds common general prescribed limits and does not fall "
                "under the current Class 1 or Class 2 paths."
            )
        elif template_id == "PM_SEMI":
            reason = (
                "The prime mover and semitrailer combination exceeds common general prescribed "
                "limits and does not fall under the current Class 1 or Class 2 paths."
            )
        elif template_id == "B_DOUBLE":
            reason = (
                "The B-double exceeds the prototype limits applied to this Class 2 category. "
                "Under the current prototype logic, it is flagged as Class 3 for further compliance review."
            )
        else:
            reason = "The vehicle exceeds the configured dimension limits."

        return {
            "status": "ok",
            "classification": dimension_rule.classification_if_exceeded_limit,
            "reason": reason,
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": limit_check["reasons"] + warnings
        }

    if template_id == "RIGID_TRUCK":
        return {
            "status": "ok",
            "classification": "general_access",
            "reason": "The rigid truck is within common general limits.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": warnings
        }

    if template_id == "PM_SEMI":
        return {
            "status": "ok",
            "classification": "general_access",
            "reason": "The prime mover and semitrailer combination is within common general limits.",
            "used_dimensions": dimensions,
            "missing_fields": [],
            "warnings": warnings
        }

    if template_id == "B_DOUBLE":
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