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


from .db_models import (
    VehicleProfile,
    AxleConfiguration,
    DimensionRule,
)


def get_number_from_answers(answers, possible_keys):
    for key in possible_keys:
        value = answers.get(key)
        if value is not None and value != "":
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

    return None


from .db_models import (
    VehicleProfile,
    AxleConfiguration,
    DimensionRule,
)


def get_number_from_answers(answers, possible_keys):
    for key in possible_keys:
        value = answers.get(key)
        if value is not None and value != "":
            try:
                return float(value)
            except (TypeError, ValueError):
                return None

    return None


def classify_hvnl_from_db(
    db,
    profile_id,
    axle_config_id=None,
    custom_dimensions=False,
    answers=None,
):
    answers = answers or {}

    profile = (
        db.query(VehicleProfile)
        .filter(VehicleProfile.profile_id == profile_id)
        .first()
    )

    if not profile:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": "Vehicle profile not found.",
            "used_dimensions": {},
            "missing_fields": ["profile_id"],
            "warnings": [],
        }

    dimension_rule = (
        db.query(DimensionRule)
        .filter(DimensionRule.template_id == profile.template_id)
        .first()
    )

    if not dimension_rule:
        return {
            "status": "error",
            "classification": "unknown",
            "reason": f"No dimension rule found for template {profile.template_id}.",
            "used_dimensions": {},
            "missing_fields": [],
            "warnings": [],
        }

    axle_config = None
    if axle_config_id:
        axle_config = (
            db.query(AxleConfiguration)
            .filter(AxleConfiguration.axle_config_id == axle_config_id)
            .first()
        )

        if not axle_config:
            return {
                "status": "error",
                "classification": "unknown",
                "reason": "Axle configuration not found.",
                "used_dimensions": {},
                "missing_fields": ["axle_config_id"],
                "warnings": [],
            }

    # Use selected axle config length when available.
    # This fixes B-double 7 axle = 19 m, while 8/9 axle = 26 m.
    selected_length_limit_m = (
        float(axle_config.max_length_m)
        if axle_config and axle_config.max_length_m is not None
        else float(dimension_rule.length_limit_m)
    )

    width_limit_m = float(dimension_rule.width_limit_m)
    height_limit_m = float(dimension_rule.height_limit_m)
    length_limit_m = selected_length_limit_m

    if custom_dimensions:
        width_m = get_number_from_answers(
            answers,
            ["width_m", "overall_width_m", "custom_width_m", "width"],
        )

        height_m = get_number_from_answers(
            answers,
            ["height_m", "overall_height_m", "custom_height_m", "height"],
        )

        length_m = get_number_from_answers(
            answers,
            ["length_m", "overall_length_m", "custom_length_m", "length"],
        )

        missing_fields = []

        if width_m is None:
            missing_fields.append("width_m")

        if height_m is None:
            missing_fields.append("height_m")

        if length_m is None:
            missing_fields.append("length_m")

        if missing_fields:
            return {
                "status": "error",
                "classification": "unknown",
                "reason": "Custom dimensions are enabled but some dimension values are missing.",
                "used_dimensions": {},
                "missing_fields": missing_fields,
                "warnings": [],
            }

    else:
        width_m = float(profile.default_width_m)
        height_m = float(profile.default_height_m)

        # Important: for configurable vehicles, default length should follow selected axle config.
        if axle_config and axle_config.max_length_m is not None:
            length_m = float(axle_config.max_length_m)
        else:
            length_m = float(profile.default_length_m)

    warnings = []

    if width_m > width_limit_m:
        warnings.append(
            f"Width {width_m} m exceeds limit of {width_limit_m} m."
        )

    if height_m > height_limit_m:
        warnings.append(
            f"Height {height_m} m exceeds limit of {height_limit_m} m."
        )

    if length_m > length_limit_m:
        warnings.append(
            f"Length {length_m} m exceeds selected axle configuration limit of {length_limit_m} m."
        )

    used_dimensions = {
        "width_m": width_m,
        "height_m": height_m,
        "length_m": length_m,
        "width_limit_m": width_limit_m,
        "height_limit_m": height_limit_m,
        "length_limit_m": length_limit_m,
        "selected_axle_config_id": axle_config.axle_config_id if axle_config else None,
        "selected_axle_config_display_name": axle_config.display_name if axle_config else None,
    }

    if warnings:
        return {
            "status": "ok",
            "classification": dimension_rule.classification_if_exceeded_limit or "class_3",
            "reason": "One or more vehicle dimensions exceed the configured dimension rule or selected axle configuration limit.",
            "used_dimensions": used_dimensions,
            "missing_fields": [],
            "warnings": warnings,
        }

    if axle_config:
        return {
            "status": "ok",
            "classification": axle_config.access_path,
            "reason": f"Vehicle complies with the configured dimension rule and selected axle configuration limit for {profile.display_name}.",
            "used_dimensions": used_dimensions,
            "missing_fields": [],
            "warnings": [],
        }

    return {
        "status": "ok",
        "classification": "general_access",
        "reason": f"Vehicle complies with the configured dimension rule for {profile.display_name}.",
        "used_dimensions": used_dimensions,
        "missing_fields": [],
        "warnings": [],
    }