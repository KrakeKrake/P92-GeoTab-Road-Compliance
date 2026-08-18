from flask import Blueprint, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import pbkdf2_sha256
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError

from .database import SessionLocal
from .db_classifier import classify_hvnl_from_db
from .db_models import (
    VehicleCategory,
    VehicleProfile,
    VehicleTemplate,
    TemplateQuestion,
    LicenceClass,
    AxleConfiguration,
    AxleGroupMass,
    MassScheme,
    AxleConfigMassLimit,
    DimensionRule,
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
def to_float(value, field_name, allow_none=False):
    if value is None or value == "":
        if allow_none:
            return None
        raise ValueError(f"{field_name} is required.")

    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a number.")


def to_int(value, field_name, allow_none=False):
    if value is None or value == "":
        if allow_none:
            return None
        raise ValueError(f"{field_name} is required.")

    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be an integer.")


def normalise_id(value):
    return (value or "").strip().upper().replace(" ", "_").replace("-", "_")


@compliance_bp.route("/admin/vehicles", methods=["POST"])
def admin_add_vehicle():
    raw_body = request.get_data(as_text=True)
    print("ADMIN ADD VEHICLE RAW BODY:")
    print(raw_body)

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "detail": "Invalid or empty JSON body.",
            "raw_body": raw_body,
        }), 400

    category = data.get("category") or {}
    template = data.get("template") or {}
    profile = data.get("profile") or {}
    dimension_rule = data.get("dimension_rule") or {}
    sanity_range = data.get("input_sanity_range") or {}
    axle_configs = data.get("axle_configurations") or []

    allowed_access_paths = {"general_access", "class_1", "class_2", "class_3"}
    allowed_licences = {"LR", "MR", "HR", "HC", "MC"}

    try:
        category_id = normalise_id(category.get("category_id")).lower()
        category_name = (category.get("category_name") or "").strip()

        template_id = normalise_id(template.get("template_id"))
        template_name = (template.get("template_name") or "").strip()
        base_type = (template.get("base_type") or "").strip().lower()

        profile_id = normalise_id(profile.get("profile_id"))
        display_name = (profile.get("display_name") or "").strip()
        vehicle_family = (profile.get("vehicle_family") or "").strip()
        combination_type = (profile.get("combination_type") or "").strip()
        gvm_category = (profile.get("gvm_category") or "").strip() or None
        axle_count = to_int(profile.get("axle_count"), "axle_count", allow_none=True)
        axle_configurable = bool(profile.get("axle_configurable", True))

        default_width_m = to_float(profile.get("default_width_m"), "default_width_m")
        default_height_m = to_float(profile.get("default_height_m"), "default_height_m")
        default_length_m = to_float(profile.get("default_length_m"), "default_length_m")

        allow_custom_dimensions = bool(profile.get("allow_custom_dimensions", True))
        required_licence_class_id = normalise_id(profile.get("required_licence_class_id"))

        width_limit_m = to_float(dimension_rule.get("width_limit_m"), "width_limit_m")
        height_limit_m = to_float(dimension_rule.get("height_limit_m"), "height_limit_m")
        length_limit_m = to_float(dimension_rule.get("length_limit_m"), "length_limit_m")
        classification_if_exceeded_limit = (
            dimension_rule.get("classification_if_exceeded_limit") or "class_3"
        ).strip()
        rule_note = (dimension_rule.get("note") or "").strip() or None
        rule_name = (
            dimension_rule.get("rule_name")
            or f"{template_name} dimension rule"
        ).strip()

        min_width_m = to_float(sanity_range.get("min_width_m"), "min_width_m")
        max_width_m = to_float(sanity_range.get("max_width_m"), "max_width_m")
        min_height_m = to_float(sanity_range.get("min_height_m"), "min_height_m")
        max_height_m = to_float(sanity_range.get("max_height_m"), "max_height_m")
        min_length_m = to_float(sanity_range.get("min_length_m"), "min_length_m")
        max_length_m = to_float(sanity_range.get("max_length_m"), "max_length_m")

    except ValueError as error:
        return jsonify({"detail": str(error)}), 400

    # Required field validation
    if not category_id:
        return jsonify({"detail": "category_id is required."}), 400

    if not category_name:
        return jsonify({"detail": "category_name is required."}), 400

    if not template_id:
        return jsonify({"detail": "template_id is required."}), 400

    if not template_name:
        return jsonify({"detail": "template_name is required."}), 400

    if not base_type:
        return jsonify({"detail": "base_type is required."}), 400

    if not profile_id:
        return jsonify({"detail": "profile_id is required."}), 400

    if not display_name:
        return jsonify({"detail": "display_name is required."}), 400

    if not vehicle_family:
        return jsonify({"detail": "vehicle_family is required."}), 400

    if not combination_type:
        return jsonify({"detail": "combination_type is required."}), 400

    if required_licence_class_id not in allowed_licences:
        return jsonify({"detail": "required_licence_class_id must be LR, MR, HR, HC, or MC."}), 400

    if classification_if_exceeded_limit not in allowed_access_paths:
        return jsonify({"detail": "classification_if_exceeded_limit must be general_access, class_1, class_2, or class_3."}), 400

    if min_width_m > max_width_m:
        return jsonify({"detail": "Minimum width cannot be greater than maximum width."}), 400

    if min_height_m > max_height_m:
        return jsonify({"detail": "Minimum height cannot be greater than maximum height."}), 400

    if min_length_m > max_length_m:
        return jsonify({"detail": "Minimum length cannot be greater than maximum length."}), 400

    if not (min_width_m <= default_width_m <= max_width_m):
        return jsonify({"detail": "Default width must be within the input sanity width range."}), 400

    if not (min_height_m <= default_height_m <= max_height_m):
        return jsonify({"detail": "Default height must be within the input sanity height range."}), 400

    if not (min_length_m <= default_length_m <= max_length_m):
        return jsonify({"detail": "Default length must be within the input sanity length range."}), 400

    if width_limit_m > max_width_m:
        return jsonify({"detail": "Width legal limit cannot be greater than maximum sanity width."}), 400

    if height_limit_m > max_height_m:
        return jsonify({"detail": "Height legal limit cannot be greater than maximum sanity height."}), 400

    if length_limit_m > max_length_m:
        return jsonify({"detail": "Length legal limit cannot be greater than maximum sanity length."}), 400

    if axle_configurable and not axle_configs:
        return jsonify({"detail": "At least one axle configuration is required."}), 400

    db = get_db_session()

    try:
        # Prevent editing existing vehicle profiles
        existing_profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == profile_id)
            .first()
        )

        if existing_profile:
            return jsonify({"detail": "profile_id already exists. This page only supports adding new vehicles."}), 400

        # For MVP, require new template to avoid accidentally editing existing vehicle type behaviour
        existing_template = (
            db.query(VehicleTemplate)
            .filter(VehicleTemplate.template_id == template_id)
            .first()
        )

        if existing_template:
            return jsonify({
                "detail": "template_id already exists. For the add-new-vehicle page, create a new template_id to avoid modifying existing vehicle types."
            }), 400

        licence = (
            db.query(LicenceClass)
            .filter(LicenceClass.licence_class_id == required_licence_class_id)
            .first()
        )

        if not licence:
            return jsonify({"detail": "Invalid required licence class."}), 400

        category_row = (
            db.query(VehicleCategory)
            .filter(VehicleCategory.category_id == category_id)
            .first()
        )

        if not category_row:
            category_row = VehicleCategory(
                category_id=category_id,
                category_name=category_name,
            )
            db.add(category_row)

        template_row = VehicleTemplate(
            template_id=template_id,
            template_name=template_name,
            base_type=base_type,
        )
        db.add(template_row)
        # Important: insert category and template first
        # before inserting profile, dimension rules, sanity ranges, and axle configs
        db.flush()


        profile_row = VehicleProfile(
            profile_id=profile_id,
            display_name=display_name,
            category_id=category_id,
            template_id=template_id,
            vehicle_family=vehicle_family,
            combination_type=combination_type,
            gvm_category=gvm_category,
            axle_count=axle_count,
            axle_configurable=axle_configurable,
            default_width_m=default_width_m,
            default_height_m=default_height_m,
            default_length_m=default_length_m,
            allow_custom_dimensions=allow_custom_dimensions,
            required_licence_class_id=required_licence_class_id,
        )
        db.add(profile_row)

        dimension_rule_row = DimensionRule(
            template_id=template_id,
            rule_name=rule_name,
            width_limit_m=width_limit_m,
            height_limit_m=height_limit_m,
            length_limit_m=length_limit_m,
            classification_if_exceeded_limit=classification_if_exceeded_limit,
            note=rule_note,
        )
        db.add(dimension_rule_row)

        sanity_row = InputSanityRange(
            template_id=template_id,
            min_width_m=min_width_m,
            max_width_m=max_width_m,
            min_height_m=min_height_m,
            max_height_m=max_height_m,
            min_length_m=min_length_m,
            max_length_m=max_length_m,
        )
        db.add(sanity_row)
        # Force parent records to be inserted first before child records
        db.flush()

        seen_axle_config_ids = set()

        for index, config in enumerate(axle_configs, start=1):
            axle_config_id = normalise_id(config.get("axle_config_id"))
            axle_display_name = (config.get("display_name") or "").strip()
            access_path = (config.get("access_path") or "").strip()
            note = (config.get("note") or "").strip() or None

            try:
                axle_max_length_m = to_float(config.get("max_length_m"), f"axle_configurations[{index}].max_length_m")                
                gml_mass_t = to_float(config.get("gml_mass_t"), f"axle_configurations[{index}].gml_mass_t", allow_none=True)
                cml_mass_t = to_float(config.get("cml_mass_t"), f"axle_configurations[{index}].cml_mass_t", allow_none=True)
                hml_mass_t = to_float(config.get("hml_mass_t"), f"axle_configurations[{index}].hml_mass_t", allow_none=True)
            except ValueError as error:
                return jsonify({"detail": str(error)}), 400

            if not axle_config_id:
                return jsonify({"detail": f"axle_configurations[{index}].axle_config_id is required."}), 400

            if axle_config_id in seen_axle_config_ids:
                return jsonify({"detail": f"Duplicate axle_config_id in request: {axle_config_id}"}), 400

            seen_axle_config_ids.add(axle_config_id)

            existing_config = (
                db.query(AxleConfiguration)
                .filter(AxleConfiguration.axle_config_id == axle_config_id)
                .first()
            )

            if existing_config:
                return jsonify({"detail": f"axle_config_id already exists: {axle_config_id}"}), 400

            if not axle_display_name:
                return jsonify({"detail": f"axle_configurations[{index}].display_name is required."}), 400

            if access_path not in allowed_access_paths:
                return jsonify({
                    "detail": f"axle_configurations[{index}].access_path must be general_access, class_1, class_2, or class_3."
                }), 400

            if not (min_length_m <= axle_max_length_m <= max_length_m):
                return jsonify({
                    "detail": f"Axle configuration max length for {axle_config_id} must be within the input sanity length range."
                }), 400

            for mass_value, field_name in [
                (gml_mass_t, "GML"),
                (cml_mass_t, "CML"),
                (hml_mass_t, "HML"),
            ]:
            
                if mass_value is not None and mass_value < 0:
                    return jsonify({"detail": f"{field_name} mass cannot be negative for {axle_config_id}."}), 400

            axle_config_row = AxleConfiguration(
                axle_config_id=axle_config_id,
                template_id=template_id,
                display_name=axle_display_name,
                max_length_m=axle_max_length_m,
                access_path=access_path,
                note=note,
            )
            db.add(axle_config_row)
            # Force axle configuration to exist before inserting axle group masses and mass limits
            db.flush()
            

            group_masses = config.get("axle_group_masses_t") or []
            for group_index, group_mass in enumerate(group_masses, start=1):
                group_mass_t = to_float(group_mass, f"{axle_config_id}.axle_group_masses_t[{group_index}]")

                db.add(AxleGroupMass(
                    axle_config_id=axle_config_id,
                    group_order=group_index,
                    mass_t=group_mass_t,
                ))

            for scheme_id, mass_value in [
                ("GML", gml_mass_t),
                ("CML", cml_mass_t),
                ("HML", hml_mass_t),
            ]:
                db.add(AxleConfigMassLimit(
                    axle_config_id=axle_config_id,
                    mass_scheme_id=scheme_id,
                    mass_limit_t=mass_value,
                ))

        db.commit()

        return jsonify({
            "message": "Vehicle added successfully.",
            "profile_id": profile_id,
            "template_id": template_id,
            "axle_config_count": len(axle_configs),
        }), 201

    except IntegrityError as error:
        db.rollback()
        return jsonify({
            "detail": "Database integrity error. Check duplicate IDs and foreign key values.",
            "error": str(error),
        }), 400

    except Exception as error:
        db.rollback()
        return jsonify({
            "detail": "Failed to add vehicle.",
            "error": str(error),
        }), 500

    finally:
        db.close()

def serialize_admin_vehicle(db, profile_id):
    profile = (
        db.query(VehicleProfile)
        .filter(VehicleProfile.profile_id == profile_id)
        .first()
    )

    if not profile:
        return None

    category = (
        db.query(VehicleCategory)
        .filter(VehicleCategory.category_id == profile.category_id)
        .first()
    )

    template = (
        db.query(VehicleTemplate)
        .filter(VehicleTemplate.template_id == profile.template_id)
        .first()
    )

    dimension_rule = (
        db.query(DimensionRule)
        .filter(DimensionRule.template_id == profile.template_id)
        .first()
    )

    sanity_range = (
        db.query(InputSanityRange)
        .filter(InputSanityRange.template_id == profile.template_id)
        .first()
    )

    axle_configs = (
        db.query(AxleConfiguration)
        .filter(AxleConfiguration.template_id == profile.template_id)
        .order_by(AxleConfiguration.display_name)
        .all()
    )

    axle_config_payload = []

    for config in axle_configs:
        group_masses = (
            db.query(AxleGroupMass)
            .filter(AxleGroupMass.axle_config_id == config.axle_config_id)
            .order_by(AxleGroupMass.group_order)
            .all()
        )

        mass_limits = (
            db.query(AxleConfigMassLimit)
            .filter(AxleConfigMassLimit.axle_config_id == config.axle_config_id)
            .all()
        )

        mass_limit_map = {
            limit.mass_scheme_id: limit.mass_limit_t
            for limit in mass_limits
        }

        axle_config_payload.append({
            "axle_config_id": config.axle_config_id,
            "display_name": config.display_name,
            "max_length_m": float(config.max_length_m),
            "access_path": config.access_path,
            "axle_group_masses_csv": ", ".join(
                str(float(group.mass_t)).rstrip("0").rstrip(".")
                for group in group_masses
            ),
            "gml_mass_t": (
                float(mass_limit_map["GML"])
                if mass_limit_map.get("GML") is not None
                else ""
            ),
            "cml_mass_t": (
                float(mass_limit_map["CML"])
                if mass_limit_map.get("CML") is not None
                else ""
            ),
            "hml_mass_t": (
                float(mass_limit_map["HML"])
                if mass_limit_map.get("HML") is not None
                else ""
            ),
            "note": config.note or "",
        })

    return {
        "category": {
            "category_id": category.category_id if category else profile.category_id,
            "category_name": category.category_name if category else "",
        },
        "template": {
            "template_id": template.template_id if template else profile.template_id,
            "template_name": template.template_name if template else "",
            "base_type": template.base_type if template else "",
        },
        "profile": {
            "profile_id": profile.profile_id,
            "display_name": profile.display_name,
            "vehicle_family": profile.vehicle_family,
            "combination_type": profile.combination_type,
            "gvm_category": profile.gvm_category or "",
            "axle_count": profile.axle_count if profile.axle_count is not None else "",
            "axle_configurable": profile.axle_configurable,
            "default_width_m": float(profile.default_width_m),
            "default_height_m": float(profile.default_height_m),
            "default_length_m": float(profile.default_length_m),
            "allow_custom_dimensions": profile.allow_custom_dimensions,
            "required_licence_class_id": profile.required_licence_class_id,
        },
        "dimension_rule": {
            "rule_name": dimension_rule.rule_name if dimension_rule else "",
            "width_limit_m": float(dimension_rule.width_limit_m) if dimension_rule else "",
            "height_limit_m": float(dimension_rule.height_limit_m) if dimension_rule else "",
            "length_limit_m": float(dimension_rule.length_limit_m) if dimension_rule else "",
            "classification_if_exceeded_limit": (
                dimension_rule.classification_if_exceeded_limit
                if dimension_rule
                else "class_3"
            ),
            "note": dimension_rule.note if dimension_rule and dimension_rule.note else "",
        },
        "input_sanity_range": {
            "min_width_m": float(sanity_range.min_width_m) if sanity_range else "",
            "max_width_m": float(sanity_range.max_width_m) if sanity_range else "",
            "min_height_m": float(sanity_range.min_height_m) if sanity_range else "",
            "max_height_m": float(sanity_range.max_height_m) if sanity_range else "",
            "min_length_m": float(sanity_range.min_length_m) if sanity_range else "",
            "max_length_m": float(sanity_range.max_length_m) if sanity_range else "",
        },
        "axle_configurations": axle_config_payload,
    }


@compliance_bp.route("/admin/vehicles", methods=["GET"])
def admin_list_vehicles():
    db = get_db_session()

    try:
        profiles = (
            db.query(VehicleProfile)
            .order_by(VehicleProfile.display_name)
            .all()
        )

        return jsonify([
            {
                "profile_id": profile.profile_id,
                "display_name": profile.display_name,
                "template_id": profile.template_id,
                "required_licence_class_id": profile.required_licence_class_id,
            }
            for profile in profiles
        ])

    finally:
        db.close()


@compliance_bp.route("/admin/vehicles/<profile_id>", methods=["GET"])
def admin_get_vehicle(profile_id):
    db = get_db_session()

    try:
        profile_id = normalise_id(profile_id)
        data = serialize_admin_vehicle(db, profile_id)

        if not data:
            return jsonify({"detail": "Vehicle profile not found."}), 404

        return jsonify(data)

    finally:
        db.close()


@compliance_bp.route("/admin/vehicles/<profile_id>", methods=["PUT"])
def admin_update_vehicle(profile_id):
    raw_body = request.get_data(as_text=True)
    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "detail": "Invalid or empty JSON body.",
            "raw_body": raw_body,
        }), 400

    profile_id = normalise_id(profile_id)

    category = data.get("category") or {}
    template = data.get("template") or {}
    profile = data.get("profile") or {}
    dimension_rule = data.get("dimension_rule") or {}
    sanity_range = data.get("input_sanity_range") or {}
    axle_configs = data.get("axle_configurations") or []

    allowed_access_paths = {"general_access", "class_1", "class_2", "class_3"}
    allowed_licences = {"LR", "MR", "HR", "HC", "MC"}

    try:
        payload_profile_id = normalise_id(profile.get("profile_id") or profile_id)
        payload_template_id = normalise_id(template.get("template_id"))
        payload_category_id = normalise_id(category.get("category_id")).lower()

        category_name = (category.get("category_name") or "").strip()
        template_name = (template.get("template_name") or "").strip()
        base_type = (template.get("base_type") or "").strip().lower()

        display_name = (profile.get("display_name") or "").strip()
        vehicle_family = (profile.get("vehicle_family") or "").strip()
        combination_type = (profile.get("combination_type") or "").strip()
        gvm_category = (profile.get("gvm_category") or "").strip() or None
        axle_count = to_int(profile.get("axle_count"), "axle_count", allow_none=True)
        axle_configurable = bool(profile.get("axle_configurable", True))

        default_width_m = to_float(profile.get("default_width_m"), "default_width_m")
        default_height_m = to_float(profile.get("default_height_m"), "default_height_m")
        default_length_m = to_float(profile.get("default_length_m"), "default_length_m")

        allow_custom_dimensions = bool(profile.get("allow_custom_dimensions", True))
        required_licence_class_id = normalise_id(profile.get("required_licence_class_id"))

        rule_name = (dimension_rule.get("rule_name") or "").strip()
        width_limit_m = to_float(dimension_rule.get("width_limit_m"), "width_limit_m")
        height_limit_m = to_float(dimension_rule.get("height_limit_m"), "height_limit_m")
        length_limit_m = to_float(dimension_rule.get("length_limit_m"), "length_limit_m")
        classification_if_exceeded_limit = (
            dimension_rule.get("classification_if_exceeded_limit") or "class_3"
        ).strip()
        rule_note = (dimension_rule.get("note") or "").strip() or None

        min_width_m = to_float(sanity_range.get("min_width_m"), "min_width_m")
        max_width_m = to_float(sanity_range.get("max_width_m"), "max_width_m")
        min_height_m = to_float(sanity_range.get("min_height_m"), "min_height_m")
        max_height_m = to_float(sanity_range.get("max_height_m"), "max_height_m")
        min_length_m = to_float(sanity_range.get("min_length_m"), "min_length_m")
        max_length_m = to_float(sanity_range.get("max_length_m"), "max_length_m")

    except ValueError as error:
        return jsonify({"detail": str(error)}), 400

    if payload_profile_id != profile_id:
        return jsonify({
            "detail": "profile_id cannot be changed on the edit page. Create a new vehicle instead."
        }), 400

    if not category_name:
        return jsonify({"detail": "category_name is required."}), 400

    if not template_name:
        return jsonify({"detail": "template_name is required."}), 400

    if not base_type:
        return jsonify({"detail": "base_type is required."}), 400

    if not display_name:
        return jsonify({"detail": "display_name is required."}), 400

    if not vehicle_family:
        return jsonify({"detail": "vehicle_family is required."}), 400

    if not combination_type:
        return jsonify({"detail": "combination_type is required."}), 400

    if required_licence_class_id not in allowed_licences:
        return jsonify({"detail": "required_licence_class_id must be LR, MR, HR, HC, or MC."}), 400

    if classification_if_exceeded_limit not in allowed_access_paths:
        return jsonify({
            "detail": "classification_if_exceeded_limit must be general_access, class_1, class_2, or class_3."
        }), 400

    if min_width_m > max_width_m:
        return jsonify({"detail": "Minimum width cannot be greater than maximum width."}), 400

    if min_height_m > max_height_m:
        return jsonify({"detail": "Minimum height cannot be greater than maximum height."}), 400

    if min_length_m > max_length_m:
        return jsonify({"detail": "Minimum length cannot be greater than maximum length."}), 400

    if not (min_width_m <= default_width_m <= max_width_m):
        return jsonify({"detail": "Default width must be within the input sanity width range."}), 400

    if not (min_height_m <= default_height_m <= max_height_m):
        return jsonify({"detail": "Default height must be within the input sanity height range."}), 400

    if not (min_length_m <= default_length_m <= max_length_m):
        return jsonify({"detail": "Default length must be within the input sanity length range."}), 400

    if width_limit_m > max_width_m:
        return jsonify({"detail": "Width legal limit cannot be greater than maximum sanity width."}), 400

    if height_limit_m > max_height_m:
        return jsonify({"detail": "Height legal limit cannot be greater than maximum sanity height."}), 400

    if length_limit_m > max_length_m:
        return jsonify({"detail": "Length legal limit cannot be greater than maximum sanity length."}), 400

    if axle_configurable and not axle_configs:
        return jsonify({"detail": "At least one axle configuration is required."}), 400

    db = get_db_session()

    try:
        existing_profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == profile_id)
            .first()
        )

        if not existing_profile:
            return jsonify({"detail": "Vehicle profile not found."}), 404

        if payload_template_id != existing_profile.template_id:
            return jsonify({
                "detail": "template_id cannot be changed on the edit page."
            }), 400

        if payload_category_id != existing_profile.category_id:
            return jsonify({
                "detail": "category_id cannot be changed on the edit page."
            }), 400

        licence = (
            db.query(LicenceClass)
            .filter(LicenceClass.licence_class_id == required_licence_class_id)
            .first()
        )

        if not licence:
            return jsonify({"detail": "Invalid required licence class."}), 400

        category_row = (
            db.query(VehicleCategory)
            .filter(VehicleCategory.category_id == existing_profile.category_id)
            .first()
        )

        if category_row:
            category_row.category_name = category_name

        template_row = (
            db.query(VehicleTemplate)
            .filter(VehicleTemplate.template_id == existing_profile.template_id)
            .first()
        )

        if template_row:
            template_row.template_name = template_name
            template_row.base_type = base_type

        existing_profile.display_name = display_name
        existing_profile.vehicle_family = vehicle_family
        existing_profile.combination_type = combination_type
        existing_profile.gvm_category = gvm_category
        existing_profile.axle_count = axle_count
        existing_profile.axle_configurable = axle_configurable
        existing_profile.default_width_m = default_width_m
        existing_profile.default_height_m = default_height_m
        existing_profile.default_length_m = default_length_m
        existing_profile.allow_custom_dimensions = allow_custom_dimensions
        existing_profile.required_licence_class_id = required_licence_class_id

        dimension_rule_row = (
            db.query(DimensionRule)
            .filter(DimensionRule.template_id == existing_profile.template_id)
            .first()
        )

        if not dimension_rule_row:
            dimension_rule_row = DimensionRule(template_id=existing_profile.template_id)
            db.add(dimension_rule_row)

        dimension_rule_row.rule_name = rule_name or f"{template_name} dimension rule"
        dimension_rule_row.width_limit_m = width_limit_m
        dimension_rule_row.height_limit_m = height_limit_m
        dimension_rule_row.length_limit_m = length_limit_m
        dimension_rule_row.classification_if_exceeded_limit = classification_if_exceeded_limit
        dimension_rule_row.note = rule_note

        sanity_row = (
            db.query(InputSanityRange)
            .filter(InputSanityRange.template_id == existing_profile.template_id)
            .first()
        )

        if not sanity_row:
            sanity_row = InputSanityRange(template_id=existing_profile.template_id)
            db.add(sanity_row)

        sanity_row.min_width_m = min_width_m
        sanity_row.max_width_m = max_width_m
        sanity_row.min_height_m = min_height_m
        sanity_row.max_height_m = max_height_m
        sanity_row.min_length_m = min_length_m
        sanity_row.max_length_m = max_length_m

        db.flush()

        seen_axle_config_ids = set()

        for index, config in enumerate(axle_configs, start=1):
            axle_config_id = normalise_id(config.get("axle_config_id"))
            axle_display_name = (config.get("display_name") or "").strip()
            access_path = (config.get("access_path") or "").strip()
            note = (config.get("note") or "").strip() or None

            try:
                axle_max_length_m = to_float(
                    config.get("max_length_m"),
                    f"axle_configurations[{index}].max_length_m"
                )

                gml_mass_t = to_float(
                    config.get("gml_mass_t"),
                    f"axle_configurations[{index}].gml_mass_t",
                    allow_none=True
                )

                cml_mass_t = to_float(
                    config.get("cml_mass_t"),
                    f"axle_configurations[{index}].cml_mass_t",
                    allow_none=True
                )

                hml_mass_t = to_float(
                    config.get("hml_mass_t"),
                    f"axle_configurations[{index}].hml_mass_t",
                    allow_none=True
                )

            except ValueError as error:
                return jsonify({"detail": str(error)}), 400

            if not axle_config_id:
                return jsonify({
                    "detail": f"axle_configurations[{index}].axle_config_id is required."
                }), 400

            if axle_config_id in seen_axle_config_ids:
                return jsonify({
                    "detail": f"Duplicate axle_config_id in request: {axle_config_id}"
                }), 400

            seen_axle_config_ids.add(axle_config_id)

            if not axle_display_name:
                return jsonify({
                    "detail": f"axle_configurations[{index}].display_name is required."
                }), 400

            if access_path not in allowed_access_paths:
                return jsonify({
                    "detail": f"axle_configurations[{index}].access_path must be general_access, class_1, class_2, or class_3."
                }), 400

            if not (min_length_m <= axle_max_length_m <= max_length_m):
                return jsonify({
                    "detail": f"Axle configuration max length for {axle_config_id} must be within the input sanity length range."
                }), 400

            group_masses = config.get("axle_group_masses_t")

            if group_masses is None:
                group_masses_csv = config.get("axle_group_masses_csv") or ""
                group_masses = [
                    value.strip()
                    for value in group_masses_csv.split(",")
                    if value.strip()
                ]

            if not group_masses:
                return jsonify({
                    "detail": f"At least one axle group mass is required for {axle_config_id}."
                }), 400

            for mass_value, field_name in [
                (gml_mass_t, "GML"),
                (cml_mass_t, "CML"),
                (hml_mass_t, "HML"),
            ]:
                if mass_value is not None and mass_value < 0:
                    return jsonify({
                        "detail": f"{field_name} mass cannot be negative for {axle_config_id}."
                    }), 400

            config_row = (
                db.query(AxleConfiguration)
                .filter(AxleConfiguration.axle_config_id == axle_config_id)
                .first()
            )

            if config_row and config_row.template_id != existing_profile.template_id:
                return jsonify({
                    "detail": f"Axle config {axle_config_id} belongs to another template and cannot be edited here."
                }), 400

            if not config_row:
                config_row = AxleConfiguration(
                    axle_config_id=axle_config_id,
                    template_id=existing_profile.template_id,
                )
                db.add(config_row)
                db.flush()

            config_row.display_name = axle_display_name
            config_row.max_length_m = axle_max_length_m
            config_row.access_path = access_path
            config_row.note = note

            db.flush()

            db.query(AxleGroupMass).filter(
                AxleGroupMass.axle_config_id == axle_config_id
            ).delete(synchronize_session=False)

            for group_index, group_mass in enumerate(group_masses, start=1):
                group_mass_t = to_float(
                    group_mass,
                    f"{axle_config_id}.axle_group_masses_t[{group_index}]"
                )

                db.add(AxleGroupMass(
                    axle_config_id=axle_config_id,
                    group_order=group_index,
                    mass_t=group_mass_t,
                ))

            for scheme_id, mass_value in [
                ("GML", gml_mass_t),
                ("CML", cml_mass_t),
                ("HML", hml_mass_t),
            ]:
                mass_scheme = (
                    db.query(MassScheme)
                    .filter(MassScheme.mass_scheme_id == scheme_id)
                    .first()
                )

                if not mass_scheme:
                    return jsonify({
                        "detail": f"Mass scheme {scheme_id} does not exist in compliance.mass_schemes."
                    }), 400

                mass_limit_row = (
                    db.query(AxleConfigMassLimit)
                    .filter(
                        AxleConfigMassLimit.axle_config_id == axle_config_id,
                        AxleConfigMassLimit.mass_scheme_id == scheme_id,
                    )
                    .first()
                )

                if not mass_limit_row:
                    mass_limit_row = AxleConfigMassLimit(
                        axle_config_id=axle_config_id,
                        mass_scheme_id=scheme_id,
                    )
                    db.add(mass_limit_row)

                mass_limit_row.mass_limit_t = mass_value

        db.commit()

        return jsonify({
            "message": "Vehicle updated successfully.",
            "profile_id": existing_profile.profile_id,
            "template_id": existing_profile.template_id,
            "axle_config_count": len(axle_configs),
        })

    except IntegrityError as error:
        db.rollback()
        return jsonify({
            "detail": "Database integrity error. Check duplicate IDs and foreign key values.",
            "error": str(error),
        }), 400

    except Exception as error:
        db.rollback()
        return jsonify({
            "detail": "Failed to update vehicle.",
            "error": str(error),
        }), 500

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