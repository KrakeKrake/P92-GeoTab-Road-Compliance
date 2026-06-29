from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, BaseModel, EmailStr


class QuestionModel(BaseModel):
    name: str
    type: str
    label: str


class TemplateSummary(BaseModel):
    vehicle_id: str
    display_name: str


class TemplateDetailResponse(BaseModel):
    vehicle_id: str
    display_name: str
    base_type: str
    extra_questions: List[QuestionModel]


class ProfileSummary(BaseModel):
    profile_id: str
    display_name: str


class CategoryResponse(BaseModel):
    id: str
    label: str


class CategoryDetailResponse(BaseModel):
    category_id: str
    label: str
    profiles: List[ProfileSummary]


class ClassificationRequest(BaseModel):
    profile_id: str = Field(..., description="Selected vehicle profile ID")
    axle_config_id: Optional[str] = None
    custom_dimensions: bool = False
    answers: Dict[str, Any] = Field(default_factory=dict)


class ClassificationResponse(BaseModel):
    profile_id: str
    display_name: Optional[str] = None
    template_id: Optional[str] = None
    status: str
    classification: str
    reason: str
    used_dimensions: Dict[str, float] = Field(default_factory=dict)
    missing_fields: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class ProfileDetailResponse(BaseModel):
    profile_id: str
    display_name: str
    template_id: str

    vehicle_family: str
    combination_type: str
    gvm_category: Optional[str] = None
    axle_count: Optional[int] = None
    axle_configurable: bool = False
    possible_axle_configs: List[str] = Field(default_factory=list)

    default_width_m: float
    default_height_m: float
    default_length_m: float
    allow_custom_dimensions: bool

class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    licence_class_id: Optional[str] = None


class LoginRequest(BaseModel):
    login: str
    password: str


class AuthUserResponse(BaseModel):
    user_id: int
    email: str
    username: str
    licence_class_id: Optional[str] = None
    favourite_profile_id: Optional[str] = None


class AuthResponse(BaseModel):
    status: str
    message: str
    user: AuthUserResponse

class UpdateUserProfileRequest(BaseModel):
    licence_class_id: Optional[str] = None
    favourite_profile_id: Optional[str] = None