from fastapi import Depends
from sqlalchemy.orm import Session
from db_classifier import classify_hvnl_from_db
from database import get_db
from db_models import (
    VehicleProfile,
    VehicleTemplate,
    TemplateQuestion,
    LicenceClass,
    AxleConfiguration,
    AxleConfigMassLimit,
    InputSanityRange,
    User
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from classifier import classify_hvnl, get_profile, get_template
from models import (
    CategoryDetailResponse,
    CategoryResponse,
    ClassificationRequest,
    ClassificationResponse,
    ProfileDetailResponse,
    ProfileSummary,
    TemplateDetailResponse,
    SignupRequest,
    LoginRequest,
    AuthResponse,
    AuthUserResponse
)

from vehicle_categories import vehicle_categories
from vehicle_profiles import vehicle_profiles
from licence_rules import get_profiles_by_licence
from axle_configurations import axle_configurations
from mass_validator import validate_mass
from pydantic import BaseModel
from sqlalchemy import or_
from passlib.context import CryptContext
from datetime import datetime
from models import UpdateUserProfileRequest

app = FastAPI(
    title="P1 HVNL Vehicle Classifier",
    description="NHVR class path classification.",
    version="0.2.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "message": "P1 HVNL Vehicle Classifier is running.",
        "docs": "/docs"
    }


@app.get("/categories", response_model=list[CategoryResponse])
def list_categories():
    return [
        CategoryResponse(
            id=category["id"],
            label=category["label"]
        )
        for category in vehicle_categories
    ]


@app.get("/categories/{category_id}", response_model=CategoryDetailResponse)
def get_category(category_id: str):
    for category in vehicle_categories:
        if category["id"] == category_id:
            profiles = []
            for profile_id in category["profile_ids"]:
                profile = vehicle_profiles.get(profile_id)
                if profile:
                    profiles.append(
                        ProfileSummary(
                            profile_id=profile_id,
                            display_name=profile["display_name"]
                        )
                    )

            return CategoryDetailResponse(
                category_id=category_id,
                label=category["label"],
                profiles=profiles
            )

    raise HTTPException(status_code=404, detail="Category not found.")

@app.get("/profiles", response_model=list[ProfileSummary])
def list_profiles(db: Session = Depends(get_db)):
    profiles = db.query(VehicleProfile).all()

    return [
        ProfileSummary(
            profile_id=profile.profile_id,
            display_name=profile.display_name
        )
        for profile in profiles
    ]


@app.get("/profiles/{profile_id}", response_model=ProfileDetailResponse)
def get_profile_detail(profile_id: str, db: Session = Depends(get_db)):
    profile = (
        db.query(VehicleProfile)
        .filter(VehicleProfile.profile_id == profile_id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Vehicle profile not found.")

    return ProfileDetailResponse(
        profile_id=profile.profile_id,
        display_name=profile.display_name,
        template_id=profile.template_id,
        vehicle_family=profile.vehicle_family,
        combination_type=profile.combination_type,
        gvm_category=profile.gvm_category,
        axle_count=profile.axle_count,
        axle_configurable=profile.axle_configurable,
        possible_axle_configs=[],  # temporary; your DB does not store this list directly
        default_width_m=float(profile.default_width_m),
        default_height_m=float(profile.default_height_m),
        default_length_m=float(profile.default_length_m),
        allow_custom_dimensions=profile.allow_custom_dimensions
    )

@app.get("/templates/{template_id}", response_model=TemplateDetailResponse)
def get_template_detail(template_id: str, db: Session = Depends(get_db)):
    template = (
        db.query(VehicleTemplate)
        .filter(VehicleTemplate.template_id == template_id)
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="Vehicle template not found.")

    questions = (
        db.query(TemplateQuestion)
        .filter(TemplateQuestion.template_id == template_id)
        .all()
    )

    return TemplateDetailResponse(
        vehicle_id=template.template_id,
        display_name=template.template_name,
        base_type=template.base_type,
        extra_questions=[
            {
                "name": question.question_name,
                "type": question.question_type,
                "label": question.question_label
            }
            for question in questions
        ]
    )


@app.post("/classify", response_model=ClassificationResponse)
def classify_vehicle(
    request: ClassificationRequest,
    db: Session = Depends(get_db)
):
    profile = (
        db.query(VehicleProfile)
        .filter(VehicleProfile.profile_id == request.profile_id)
        .first()
    )

    if not profile:
        raise HTTPException(status_code=404, detail="Vehicle profile not found.")

    result = classify_hvnl_from_db(
        db=db,
        profile_id=request.profile_id,
        axle_config_id=request.axle_config_id,
        custom_dimensions=request.custom_dimensions,
        answers=request.answers
    )

    return ClassificationResponse(
        profile_id=request.profile_id,
        display_name=profile.display_name,
        template_id=profile.template_id,
        status=result.get("status", "error"),
        classification=result.get("classification", "unknown"),
        reason=result.get("reason", "No reason provided."),
        used_dimensions=result.get("used_dimensions", {}),
        missing_fields=result.get("missing_fields", []),
        warnings=result.get("warnings", [])
    )

@app.get("/profiles-by-licence/{licence_class}", response_model=list[ProfileSummary])
def profiles_by_licence(licence_class: str, db: Session = Depends(get_db)):
    selected_licence = (
        db.query(LicenceClass)
        .filter(LicenceClass.licence_class_id == licence_class.upper())
        .first()
    )

    if not selected_licence:
        return []

    profiles = (
        db.query(VehicleProfile)
        .join(
            LicenceClass,
            VehicleProfile.required_licence_class_id == LicenceClass.licence_class_id
        )
        .filter(LicenceClass.rank_value <= selected_licence.rank_value)
        .all()
    )

    return [
        ProfileSummary(
            profile_id=profile.profile_id,
            display_name=profile.display_name
        )
        for profile in profiles
    ]

@app.get("/axle-configs/{template_id}")
def get_axle_configs(template_id: str, db: Session = Depends(get_db)):
    configs = (
        db.query(AxleConfiguration)
        .filter(AxleConfiguration.template_id == template_id)
        .all()
    )

    if not configs:
        raise HTTPException(
            status_code=404,
            detail="No axle configurations found for this template."
        )

    return {
        "template_id": template_id,
        "axle_configurations": [
            {
                "config_id": config.axle_config_id,
                "display_name": config.display_name,
                "max_length_m": float(config.max_length_m),
                "access_path": config.access_path,
                "note": config.note
            }
            for config in configs
        ]
    }

@app.get("/axle-config-details/{axle_config_id}")
def get_axle_config_details(axle_config_id: str, db: Session = Depends(get_db)):
    config = (
        db.query(AxleConfiguration)
        .filter(AxleConfiguration.axle_config_id == axle_config_id)
        .first()
    )

    if not config:
        raise HTTPException(status_code=404, detail="Axle configuration not found.")

    mass_limits = (
        db.query(AxleConfigMassLimit)
        .filter(AxleConfigMassLimit.axle_config_id == axle_config_id)
        .all()
    )

    return {
        "axle_config_id": config.axle_config_id,
        "display_name": config.display_name,
        "max_length_m": float(config.max_length_m),
        "access_path": config.access_path,
        "note": config.note,
        "mass_limits": [
            {
                "mass_scheme_id": limit.mass_scheme_id,
                "mass_limit_t": float(limit.mass_limit_t) if limit.mass_limit_t is not None else None,
                "applicable": limit.mass_limit_t is not None
            }
            for limit in mass_limits
        ]
    }

class MassValidationRequest(BaseModel):
    axle_config_id: str
    mass_scheme: str
    operating_mass_t: float
    
@app.post("/validate-mass")
def validate_vehicle_mass(
    request: MassValidationRequest,
    db: Session = Depends(get_db)
):
    mass_scheme = request.mass_scheme.upper()

    config = (
        db.query(AxleConfiguration)
        .filter(AxleConfiguration.axle_config_id == request.axle_config_id)
        .first()
    )

    if not config:
        return {
            "status": "error",
            "compliant": False,
            "reason": "Axle configuration not found."
        }

    mass_limit = (
        db.query(AxleConfigMassLimit)
        .filter(
            AxleConfigMassLimit.axle_config_id == request.axle_config_id,
            AxleConfigMassLimit.mass_scheme_id == mass_scheme
        )
        .first()
    )

    if not mass_limit:
        return {
            "status": "error",
            "compliant": False,
            "reason": "Invalid mass scheme. Use GML, CML, or HML."
        }

    if mass_limit.mass_limit_t is None:
        return {
            "status": "not_applicable",
            "compliant": False,
            "reason": f"{mass_scheme} does not apply to this axle configuration.",
            "selected_limit_t": None
        }

    limit = float(mass_limit.mass_limit_t)

    if request.operating_mass_t <= limit:
        return {
            "status": "ok",
            "compliant": True,
            "reason": f"Operating mass {request.operating_mass_t} t is within {mass_scheme} limit of {limit} t.",
            "selected_limit_t": limit
        }

    return {
        "status": "exceeds_limit",
        "compliant": False,
        "reason": f"Operating mass {request.operating_mass_t} t exceeds {mass_scheme} limit of {limit} t.",
        "selected_limit_t": limit
    }

@app.get("/dimension-ranges/{template_id}")
def get_dimension_ranges(template_id: str, db: Session = Depends(get_db)):
    ranges = (
        db.query(InputSanityRange)
        .filter(InputSanityRange.template_id == template_id)
        .first()
    )

    if not ranges:
        raise HTTPException(status_code=404, detail="Dimension range not found.")

    return {
        "template_id": ranges.template_id,
        "min_width_m": float(ranges.min_width_m),
        "max_width_m": float(ranges.max_width_m),
        "min_height_m": float(ranges.min_height_m),
        "max_height_m": float(ranges.max_height_m),
        "min_length_m": float(ranges.min_length_m),
        "max_length_m": float(ranges.max_length_m),
    }

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)

@app.post("/auth/signup", response_model=AuthResponse)
def signup_user(request: SignupRequest, db: Session = Depends(get_db)):
    existing_user = (
        db.query(User)
        .filter(
            or_(
                User.email == request.email,
                User.username == request.username
            )
        )
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email or username already exists."
        )

    new_user = User(
    email=request.email,
    username=request.username,
    password_hash=hash_password(request.password),
    licence_class_id=request.licence_class_id,
    created_at=datetime.now(),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return AuthResponse(
        status="success",
        message="Signup successful.",
        user=AuthUserResponse(
            user_id=new_user.user_id,
            email=new_user.email,
            username=new_user.username,
            licence_class_id=new_user.licence_class_id,
            favourite_profile_id=new_user.favourite_profile_id,
        )
    )

@app.post("/auth/login", response_model=AuthResponse)
def login_user(request: LoginRequest, db: Session = Depends(get_db)):
    user = (
        db.query(User)
        .filter(
            or_(
                User.email == request.login,
                User.username == request.login
            )
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password."
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid email/username or password."
        )

    return AuthResponse(
        status="success",
        message="Login successful.",
        user=AuthUserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            licence_class_id=user.licence_class_id,
            favourite_profile_id=user.favourite_profile_id,
        )
    )

@app.put("/auth/users/{user_id}/profile", response_model=AuthResponse)
def update_user_profile(
    user_id: int,
    request: UpdateUserProfileRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Validate licence class
    licence = (
        db.query(LicenceClass)
        .filter(LicenceClass.licence_class_id == request.licence_class_id)
        .first()
    )

    if not licence:
        raise HTTPException(status_code=400, detail="Invalid licence class.")

    # Update licence first
    user.licence_class_id = request.licence_class_id

    # Validate favourite vehicle profile if selected
    if request.favourite_profile_id:
        profile = (
            db.query(VehicleProfile)
            .filter(VehicleProfile.profile_id == request.favourite_profile_id)
            .first()
        )

        if not profile:
            raise HTTPException(status_code=400, detail="Invalid favourite vehicle profile.")

        allowed_profiles = get_profiles_by_licence(user.licence_class_id)
        allowed_profile_ids = [p["profile_id"] for p in allowed_profiles]

        if request.favourite_profile_id not in allowed_profile_ids:
            raise HTTPException(
                status_code=400,
                detail="Favourite vehicle is not allowed for this licence class."
            )

        user.favourite_profile_id = request.favourite_profile_id
    else:
        user.favourite_profile_id = None

    db.commit()
    db.refresh(user)

    return AuthResponse(
        status="success",
        message="Profile updated successfully.",
        user=AuthUserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            licence_class_id=user.licence_class_id,
            favourite_profile_id=user.favourite_profile_id,
        )
    )