from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import pbkdf2_sha256
from sqlalchemy import or_, func

from .database import SessionLocal
from .db_classifier import classify_hvnl_from_db
from .db_models import (
    VehicleProfile,
    VehicleTemplate,
    TemplateQuestion,
    LicenceClass,
    AxleConfiguration,
    AxleConfigMassLimit,
    InputSanityRange,
    User,
)

compliance_bp = Blueprint("compliance", __name__, url_prefix="/api/compliance")


def get_db_session():
    return SessionLocal()

def serialize_user(user):
    return {
        "user_id": user.user_id,
        "email": user.email,
        "username": user.username,
        "licence_class_id": user.licence_class_id,
        "favourite_profile_id": user.favourite_profile_id,
    }


@compliance_bp.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}

    email = (data.get("email") or "").strip().lower()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    licence_class_id = data.get("licence_class_id")
    favourite_profile_id = data.get("favourite_profile_id")

    if not email:
        return jsonify({"detail": "Email is required."}), 400

    if not username:
        return jsonify({"detail": "Username is required."}), 400

    if not password:
        return jsonify({"detail": "Password is required."}), 400

    db = get_db_session()
    try:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            return jsonify({"detail": "Email already exists."}), 400

        existing_username = db.query(User).filter(User.username == username).first()
        if existing_username:
            return jsonify({"detail": "Username already exists."}), 400

        if licence_class_id:
            licence = (
                db.query(LicenceClass)
                .filter(LicenceClass.licence_class_id == licence_class_id.upper())
                .first()
            )

            if not licence:
                return jsonify({"detail": "Invalid licence class."}), 400

            licence_class_id = licence_class_id.upper()

        if favourite_profile_id:
            profile = (
                db.query(VehicleProfile)
                .filter(VehicleProfile.profile_id == favourite_profile_id)
                .first()
            )

            if not profile:
                return jsonify({"detail": "Invalid favourite vehicle profile."}), 400

        user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password),
            licence_class_id=licence_class_id,
            favourite_profile_id=favourite_profile_id,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return jsonify({
            "message": "Signup successful.",
            "user": serialize_user(user),
        }), 201

    finally:
        db.close()


@compliance_bp.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    login_value = (data.get("login") or "").strip().lower()
    password = data.get("password") or ""

    if not login_value:
        return jsonify({"detail": "Email or username is required."}), 400

    if not password:
        return jsonify({"detail": "Password is required."}), 400

    db = get_db_session()
    try:
        user = (
            db.query(User)
            .filter(
                or_(
                    func.lower(User.email) == login_value,
                    func.lower(User.username) == login_value,
                )
            )
            .first()
        )

        if not user:
            return jsonify({"detail": "Invalid email/username or password."}), 401

        if not user.password_hash:
            return jsonify({"detail": "Invalid email/username or password."}), 401

        password_ok = False

        # New Werkzeug hash format, for example: scrypt:32768:8:1$...
        if user.password_hash.startswith("scrypt:") or user.password_hash.startswith("pbkdf2:"):
            try:
                password_ok = check_password_hash(user.password_hash, password)
            except ValueError:
                password_ok = False

        # Old Passlib hash format, for example: $pbkdf2-sha256$29000$...
        elif user.password_hash.startswith("$pbkdf2-sha256$"):
            try:
                password_ok = pbkdf2_sha256.verify(password, user.password_hash)

                # Proper migration: after successful login, convert old hash to new Werkzeug hash
                if password_ok:
                    user.password_hash = generate_password_hash(password)
                    db.commit()

            except Exception:
                password_ok = False

        if not password_ok:
            return jsonify({"detail": "Invalid email/username or password."}), 401

        return jsonify({
            "message": "Login successful.",
            "user": serialize_user(user),
        })

    finally:
        db.close()
        
@compliance_bp.route("/auth/users/<int:user_id>/profile", methods=["PUT"])
def update_user_profile(user_id):
    data = request.get_json() or {}

    licence_class_id = data.get("licence_class_id")
    favourite_profile_id = data.get("favourite_profile_id")

    if not licence_class_id:
        return jsonify({"detail": "licence_class_id is required."}), 400

    licence_class_id = licence_class_id.upper()

    db = get_db_session()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            return jsonify({"detail": "User not found."}), 404

        licence = (
            db.query(LicenceClass)
            .filter(LicenceClass.licence_class_id == licence_class_id)
            .first()
        )

        if not licence:
            return jsonify({"detail": "Invalid licence class."}), 400

        if favourite_profile_id:
            profile = (
                db.query(VehicleProfile)
                .filter(VehicleProfile.profile_id == favourite_profile_id)
                .first()
            )

            if not profile:
                return jsonify({"detail": "Invalid favourite vehicle profile."}), 400

            required_licence = (
                db.query(LicenceClass)
                .filter(
                    LicenceClass.licence_class_id == profile.required_licence_class_id
                )
                .first()
            )

            if required_licence and required_licence.rank_value > licence.rank_value:
                return jsonify({
                    "detail": "Selected favourite vehicle is not allowed for this licence class."
                }), 400

        user.licence_class_id = licence_class_id
        user.favourite_profile_id = favourite_profile_id or None

        db.commit()
        db.refresh(user)

        return jsonify({
            "message": "Profile updated successfully.",
            "user": serialize_user(user),
        })

    finally:
        db.close()
        
@compliance_bp.route("/profiles", methods=["GET"])
def list_profiles():
    db = get_db_session()
    try:
        profiles = db.query(VehicleProfile).all()

        return jsonify([
            {
                "profile_id": profile.profile_id,
                "display_name": profile.display_name,
            }
            for profile in profiles
        ])
    finally:
        db.close()


@compliance_bp.route("/profiles/<profile_id>", methods=["GET"])
def get_profile_detail(profile_id):
    db = get_db_session()
    try:
        profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == profile_id)
            .first()
        )

        if not profile:
            return jsonify({"detail": "Vehicle profile not found."}), 404

        return jsonify({
            "profile_id": profile.profile_id,
            "display_name": profile.display_name,
            "template_id": profile.template_id,
            "vehicle_family": profile.vehicle_family,
            "combination_type": profile.combination_type,
            "gvm_category": profile.gvm_category,
            "axle_count": profile.axle_count,
            "axle_configurable": profile.axle_configurable,
            "possible_axle_configs": [],
            "default_width_m": float(profile.default_width_m),
            "default_height_m": float(profile.default_height_m),
            "default_length_m": float(profile.default_length_m),
            "allow_custom_dimensions": profile.allow_custom_dimensions,
        })
    finally:
        db.close()


@compliance_bp.route("/templates/<template_id>", methods=["GET"])
def get_template_detail(template_id):
    db = get_db_session()
    try:
        template = (
            db.query(VehicleTemplate)
            .filter(VehicleTemplate.template_id == template_id)
            .first()
        )

        if not template:
            return jsonify({"detail": "Vehicle template not found."}), 404

        questions = (
            db.query(TemplateQuestion)
            .filter(TemplateQuestion.template_id == template_id)
            .all()
        )

        return jsonify({
            "vehicle_id": template.template_id,
            "display_name": template.template_name,
            "base_type": template.base_type,
            "extra_questions": [
                {
                    "name": question.question_name,
                    "type": question.question_type,
                    "label": question.question_label,
                }
                for question in questions
            ],
        })
    finally:
        db.close()


@compliance_bp.route("/profiles-by-licence/<licence_class>", methods=["GET"])
def profiles_by_licence(licence_class):
    db = get_db_session()
    try:
        selected_licence = (
            db.query(LicenceClass)
            .filter(LicenceClass.licence_class_id == licence_class.upper())
            .first()
        )

        if not selected_licence:
            return jsonify([])

        profiles = (
            db.query(VehicleProfile)
            .join(
                LicenceClass,
                VehicleProfile.required_licence_class_id == LicenceClass.licence_class_id,
            )
            .filter(LicenceClass.rank_value <= selected_licence.rank_value)
            .all()
        )

        return jsonify([
            {
                "profile_id": profile.profile_id,
                "display_name": profile.display_name,
            }
            for profile in profiles
        ])
    finally:
        db.close()


@compliance_bp.route("/axle-configs/<template_id>", methods=["GET"])
def get_axle_configs(template_id):
    db = get_db_session()
    try:
        configs = (
            db.query(AxleConfiguration)
            .filter(AxleConfiguration.template_id == template_id)
            .all()
        )

        if not configs:
            return jsonify({"detail": "No axle configurations found for this template."}), 404

        return jsonify({
            "template_id": template_id,
            "axle_configurations": [
                {
                    "config_id": config.axle_config_id,
                    "display_name": config.display_name,
                    "max_length_m": float(config.max_length_m),
                    "access_path": config.access_path,
                    "note": config.note,
                }
                for config in configs
            ],
        })
    finally:
        db.close()


@compliance_bp.route("/axle-config-details/<axle_config_id>", methods=["GET"])
def get_axle_config_details(axle_config_id):
    db = get_db_session()
    try:
        config = (
            db.query(AxleConfiguration)
            .filter(AxleConfiguration.axle_config_id == axle_config_id)
            .first()
        )

        if not config:
            return jsonify({"detail": "Axle configuration not found."}), 404

        mass_limits = (
            db.query(AxleConfigMassLimit)
            .filter(AxleConfigMassLimit.axle_config_id == axle_config_id)
            .all()
        )

        return jsonify({
            "config_id": config.axle_config_id,
            "display_name": config.display_name,
            "max_length_m": float(config.max_length_m),
            "access_path": config.access_path,
            "note": config.note,
            "mass_limits": [
                {
                    "mass_scheme_id": limit.mass_scheme_id,
                    "mass_limit_t": float(limit.mass_limit_t) if limit.mass_limit_t is not None else None,
                    "applicable": limit.mass_limit_t is not None,
                }
                for limit in mass_limits
            ],
        })
    finally:
        db.close()


@compliance_bp.route("/dimension-ranges/<template_id>", methods=["GET"])
def get_dimension_ranges(template_id):
    db = get_db_session()
    try:
        ranges = (
            db.query(InputSanityRange)
            .filter(InputSanityRange.template_id == template_id)
            .first()
        )

        if not ranges:
            return jsonify({"detail": "Dimension range not found."}), 404

        return jsonify({
            "template_id": ranges.template_id,
            "min_width_m": float(ranges.min_width_m),
            "max_width_m": float(ranges.max_width_m),
            "min_height_m": float(ranges.min_height_m),
            "max_height_m": float(ranges.max_height_m),
            "min_length_m": float(ranges.min_length_m),
            "max_length_m": float(ranges.max_length_m),
        })
    finally:
        db.close()



@compliance_bp.route("/vehicle-form-data/<profile_id>", methods=["GET"])
def get_vehicle_form_data(profile_id):
    db = get_db_session()
    try:
        profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == profile_id)
            .first()
        )

        if not profile:
            return jsonify({"detail": "Vehicle profile not found."}), 404

        template = (
            db.query(VehicleTemplate)
            .filter(VehicleTemplate.template_id == profile.template_id)
            .first()
        )

        questions = (
            db.query(TemplateQuestion)
            .filter(TemplateQuestion.template_id == profile.template_id)
            .all()
        )

        dimension_range = (
            db.query(InputSanityRange)
            .filter(InputSanityRange.template_id == profile.template_id)
            .first()
        )

        axle_configs = (
            db.query(AxleConfiguration)
            .filter(AxleConfiguration.template_id == profile.template_id)
            .all()
        )

        config_ids = [config.axle_config_id for config in axle_configs]

        mass_limits = []
        if config_ids:
            mass_limits = (
                db.query(AxleConfigMassLimit)
                .filter(AxleConfigMassLimit.axle_config_id.in_(config_ids))
                .all()
            )

        mass_limits_by_config = {}
        for limit in mass_limits:
            mass_limits_by_config.setdefault(limit.axle_config_id, []).append({
                "mass_scheme_id": limit.mass_scheme_id,
                "mass_limit_t": float(limit.mass_limit_t) if limit.mass_limit_t is not None else None,
                "applicable": limit.mass_limit_t is not None,
            })

        return jsonify({
            "profile": {
                "profile_id": profile.profile_id,
                "display_name": profile.display_name,
                "template_id": profile.template_id,
                "vehicle_family": profile.vehicle_family,
                "combination_type": profile.combination_type,
                "gvm_category": profile.gvm_category,
                "axle_count": profile.axle_count,
                "axle_configurable": profile.axle_configurable,
                "possible_axle_configs": [],
                "default_width_m": float(profile.default_width_m),
                "default_height_m": float(profile.default_height_m),
                "default_length_m": float(profile.default_length_m),
                "allow_custom_dimensions": profile.allow_custom_dimensions,
            },
            "template": {
                "vehicle_id": template.template_id if template else profile.template_id,
                "display_name": template.template_name if template else profile.template_id,
                "base_type": template.base_type if template else None,
                "extra_questions": [
                    {
                        "name": question.question_name,
                        "type": question.question_type,
                        "label": question.question_label,
                    }
                    for question in questions
                ],
            },
            "dimension_ranges": None if not dimension_range else {
                "template_id": dimension_range.template_id,
                "min_width_m": float(dimension_range.min_width_m),
                "max_width_m": float(dimension_range.max_width_m),
                "min_height_m": float(dimension_range.min_height_m),
                "max_height_m": float(dimension_range.max_height_m),
                "min_length_m": float(dimension_range.min_length_m),
                "max_length_m": float(dimension_range.max_length_m),
            },
            "axle_configurations": [
                {
                    "config_id": config.axle_config_id,
                    "display_name": config.display_name,
                    "max_length_m": float(config.max_length_m),
                    "access_path": config.access_path,
                    "note": config.note,
                    "mass_limits": mass_limits_by_config.get(config.axle_config_id, []),
                }
                for config in axle_configs
            ],
        })

    finally:
        db.close()


@compliance_bp.route("/classify", methods=["POST"])
def classify_vehicle():
    data = request.get_json() or {}

    profile_id = data.get("profile_id")
    axle_config_id = data.get("axle_config_id")
    custom_dimensions = data.get("custom_dimensions", False)
    answers = data.get("answers", {})

    if not profile_id:
        return jsonify({"detail": "profile_id is required."}), 400

    db = get_db_session()
    try:
        profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == profile_id)
            .first()
        )

        if not profile:
            return jsonify({"detail": "Vehicle profile not found."}), 404

        result = classify_hvnl_from_db(
            db=db,
            profile_id=profile_id,
            axle_config_id=axle_config_id,
            custom_dimensions=custom_dimensions,
            answers=answers,
        )

        return jsonify({
            "profile_id": profile_id,
            "display_name": profile.display_name,
            "template_id": profile.template_id,
            "status": result.get("status", "error"),
            "classification": result.get("classification", "unknown"),
            "reason": result.get("reason", "No reason provided."),
            "used_dimensions": result.get("used_dimensions", {}),
            "missing_fields": result.get("missing_fields", []),
            "warnings": result.get("warnings", []),
        })
    finally:
        db.close()


@compliance_bp.route("/validate-mass", methods=["POST"])
def validate_vehicle_mass():
    data = request.get_json() or {}

    axle_config_id = data.get("axle_config_id")
    mass_scheme = (data.get("mass_scheme") or "").upper()
    operating_mass_t = data.get("operating_mass_t")

    if not axle_config_id:
        return jsonify({
            "status": "error",
            "compliant": False,
            "reason": "axle_config_id is required.",
        }), 400

    if not mass_scheme:
        return jsonify({
            "status": "error",
            "compliant": False,
            "reason": "mass_scheme is required.",
        }), 400

    try:
        operating_mass_t = float(operating_mass_t)
    except (TypeError, ValueError):
        return jsonify({
            "status": "error",
            "compliant": False,
            "reason": "operating_mass_t must be a number.",
        }), 400

    db = get_db_session()
    try:
        config = (
            db.query(AxleConfiguration)
            .filter(AxleConfiguration.axle_config_id == axle_config_id)
            .first()
        )

        if not config:
            return jsonify({
                "status": "error",
                "compliant": False,
                "reason": "Axle configuration not found.",
            })

        mass_limit = (
            db.query(AxleConfigMassLimit)
            .filter(
                AxleConfigMassLimit.axle_config_id == axle_config_id,
                AxleConfigMassLimit.mass_scheme_id == mass_scheme,
            )
            .first()
        )

        if not mass_limit:
            return jsonify({
                "status": "error",
                "compliant": False,
                "reason": "Invalid mass scheme. Use GML, CML, or HML.",
            })

        if mass_limit.mass_limit_t is None:
            return jsonify({
                "status": "not_applicable",
                "compliant": False,
                "reason": f"{mass_scheme} does not apply to this axle configuration.",
                "selected_limit_t": None,
            })

        limit = float(mass_limit.mass_limit_t)

        if operating_mass_t <= limit:
            return jsonify({
                "status": "ok",
                "compliant": True,
                "reason": f"Operating mass {operating_mass_t} t is within {mass_scheme} limit of {limit} t.",
                "selected_limit_t": limit,
            })

        return jsonify({
            "status": "exceeds_limit",
            "compliant": False,
            "reason": f"Operating mass {operating_mass_t} t exceeds {mass_scheme} limit of {limit} t.",
            "selected_limit_t": limit,
        })
    finally:
        db.close()


@compliance_bp.route("/classify-and-validate", methods=["POST"])
def classify_and_validate_vehicle():
    data = request.get_json() or {}

    profile_id = data.get("profile_id")
    axle_config_id = data.get("axle_config_id")
    custom_dimensions = data.get("custom_dimensions", False)
    answers = data.get("answers", {})

    mass_scheme = (data.get("mass_scheme") or "").upper()
    operating_mass_t = data.get("operating_mass_t")

    if not profile_id:
        return jsonify({"detail": "profile_id is required."}), 400

    if not axle_config_id:
        return jsonify({"detail": "axle_config_id is required."}), 400

    if not mass_scheme:
        return jsonify({"detail": "mass_scheme is required."}), 400

    try:
        operating_mass_t = float(operating_mass_t)
    except (TypeError, ValueError):
        return jsonify({"detail": "operating_mass_t must be a number."}), 400

    db = get_db_session()
    try:
        profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == profile_id)
            .first()
        )

        if not profile:
            return jsonify({"detail": "Vehicle profile not found."}), 404

        classification_result = classify_hvnl_from_db(
            db=db,
            profile_id=profile_id,
            axle_config_id=axle_config_id,
            custom_dimensions=custom_dimensions,
            answers=answers,
        )

        mass_limit = (
            db.query(AxleConfigMassLimit)
            .filter(
                AxleConfigMassLimit.axle_config_id == axle_config_id,
                AxleConfigMassLimit.mass_scheme_id == mass_scheme,
            )
            .first()
        )

        if not mass_limit:
            mass_validation_result = {
                "status": "error",
                "compliant": False,
                "reason": "Invalid mass scheme. Use GML, CML, or HML.",
                "selected_limit_t": None,
            }

        elif mass_limit.mass_limit_t is None:
            mass_validation_result = {
                "status": "not_applicable",
                "compliant": False,
                "reason": f"{mass_scheme} does not apply to this axle configuration.",
                "selected_limit_t": None,
            }

        else:
            limit = float(mass_limit.mass_limit_t)

            if operating_mass_t <= limit:
                mass_validation_result = {
                    "status": "ok",
                    "compliant": True,
                    "reason": f"Operating mass {operating_mass_t} t is within {mass_scheme} limit of {limit} t.",
                    "selected_limit_t": limit,
                }
            else:
                mass_validation_result = {
                    "status": "exceeds_limit",
                    "compliant": False,
                    "reason": f"Operating mass {operating_mass_t} t exceeds {mass_scheme} limit of {limit} t.",
                    "selected_limit_t": limit,
                }

        return jsonify({
            "classification_result": {
                "profile_id": profile_id,
                "display_name": profile.display_name,
                "template_id": profile.template_id,
                "status": classification_result.get("status", "error"),
                "classification": classification_result.get("classification", "unknown"),
                "reason": classification_result.get("reason", "No reason provided."),
                "used_dimensions": classification_result.get("used_dimensions", {}),
                "missing_fields": classification_result.get("missing_fields", []),
                "warnings": classification_result.get("warnings", []),
            },
            "mass_validation_result": mass_validation_result,
        })

    finally:
        db.close()