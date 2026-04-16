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
    TemplateSummary,
)
from vehicle_categories import vehicle_categories
from vehicle_profiles import vehicle_profiles

app = FastAPI(
    title="P1 HVNL Vehicle Classifier",
    description="NHVR class path classification.",
    version="0.1.0"
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
def list_profiles():
    return [
        ProfileSummary(
            profile_id=profile_id,
            display_name=profile["display_name"]
        )
        for profile_id, profile in vehicle_profiles.items()
    ]


@app.get("/profiles/{profile_id}", response_model=ProfileDetailResponse)
def get_profile_detail(profile_id: str):
    profile = get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vehicle profile not found.")

    return ProfileDetailResponse(
        profile_id=profile["profile_id"],
        display_name=profile["display_name"],
        template_id=profile["template_id"],
        default_width_m=profile["default_width_m"],
        default_height_m=profile["default_height_m"],
        default_length_m=profile["default_length_m"],
        allow_custom_dimensions=profile["allow_custom_dimensions"]
    )

@app.get("/templates/{template_id}", response_model=TemplateDetailResponse)
def get_template_detail(template_id: str):
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Vehicle template not found.")

    return TemplateDetailResponse(
        vehicle_id=template_id,
        display_name=template["display_name"],
        base_type=template["base_type"],
        possible_classes=template["possible_classes"],
        extra_questions=template["extra_questions"]
    )


@app.post("/classify", response_model=ClassificationResponse)
def classify_vehicle(request: ClassificationRequest):
    profile = get_profile(request.profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Vehicle profile not found.")

    result = classify_hvnl(
        profile_id=request.profile_id,
        custom_dimensions=request.custom_dimensions,
        answers=request.answers
    )

    return ClassificationResponse(
        profile_id=request.profile_id,
        display_name=profile["display_name"],
        template_id=profile["template_id"],
        status=result.get("status", "error"),
        classification=result.get("classification", "unknown"),
        reason=result.get("reason", "No reason provided."),
        used_dimensions=result.get("used_dimensions", {}),
        missing_fields=result.get("missing_fields", []),
        warnings=result.get("warnings", [])
    )